from .primary_bootstrap import PrimaryBootstrap
from .core import Bucket
from network import PAYID,Payload
import logging
from threading import Thread
from queue import Queue
import zlib
from utils import ProgressMeter,CustomZipFile,force_json
from random import Random
from psutil import virtual_memory
from utils import get_current_commit_hash


def outplace_shuffle(l):
	# returns a shuffled l with random seed
	return outplace_shuffle.rng.sample(l,k=len(l))
outplace_shuffle.rng=Random()

class Replicator(Thread):
	"""
	Thread responsible for sending compressed batches to each replica in synchronized
	new threads
	"""
	def __init__(self,replicas,payid,total_batches):
		super().__init__(name="Replicator")
		self.progress=ProgressMeter(total_batches,"Replicator")
		self.replicas=replicas
		self.payid=payid
		self.__queue=Queue() #maybe cache

	def send_handler(payid,msock,shape,compressed):
		"""
		Send to a replicas the current chunk
		
		Args:
			payid (Payload.Id) : data network id
			msock (network.Socket): socket to send data.
			shape (tuple): batch's number of lines and columns
			compressed (bytes): compressed batch data
		"""
		msock.send(Payload(payid,(shape,compressed)))

	def run(self):
		i=0
		threads=[None for _ in self.replicas]
		while True:
			should_stop,shape,compressed = self.__queue.get()
			if should_stop:break
			print(f"t={i} sending {shape[0]} points")
			#shuffles replicas to reduce same interface distribution problem
			for j,replica in enumerate(outplace_shuffle(self.replicas)):
				thread=Thread(
					name=f"Replicator.send_handler-{i,j}",
					target=Replicator.send_handler,
					args=(self.payid,replica,shape,compressed)
				)
				threads[j]=thread
				thread.start()
			for thread in threads:
				thread.join()
			self.progress.update(1)
			i+=1

	def add_job(self,shape,compressed):
		self.__queue.put((False,shape,compressed))

	def join(self):
		self.__queue.put((True,None,None))		
		super().join()

class PrimaryGeneric(PrimaryBootstrap):
	"""
	Args:
		batch_size (int) : size of the chunks that the dataset will be splitted
	Attributes:
		winners (list): contains sockets winner for each bach index
		bucket (Bucket): contains each time, silhouete, and socket for each batch index
		BATCH_DTYPE (str): defines the type of the data stream {float32,float64}
	"""
	
	BATCH_DTYPE=None #{float32,float64}
	def preproc(self,batch):
		"""
		Function pre process batches before sending it to replicas

		Args:
			batch (np.ndarray):
		Returns:
			(np.ndarray)
		"""
		pass
	

	def __init__(self,*args,batch_size,**kwargs):
		super().__init__(*args,**kwargs)
		self.batch_size=batch_size if batch_size!=None else self.stream.chunk_size
		self.bucket=None
		self.winners={}
		
		self.__BATCH_PAYID={
			"float32":PAYID.compressed_float32_matrix,
			"float64":PAYID.compressed_float64_matrix,
		}[self.BATCH_DTYPE]
	
	def silhoete_recv_handler(self,msock):
		"""
		Helper method to recv each batch silhouete.
		updates bucket list and winners list
		
		Args:
			msock (network.Socket): socket to recv data.
		"""
		while True:
			pay=msock.recv(PAYID.end,PAYID.silhouette)
			if pay.id==PAYID.end:
				break
			# t is the batch_counter
			t,k,sil=pay.obj
			print(msock.ip,t,k,round(sil,3))
			isfull=self.bucket.add(t,k,sil,msock)
			if isfull:
				bucket_winner=self.bucket.get(t)
				print(f"winner on t={t}: {bucket_winner.msock.ip} {bucket_winner.sil:.3f} {bucket_winner.k}")
				self.winners[t]=bucket_winner

	def run(self):
		super().run(batch_size=self.batch_size)
		self.overall_timer.start()
		self.bucket=Bucket(len(self.replicas),self.total_batches)
		#---------------------------------------------------------------------------------
		#start silhoete receiver threads
		sil_threads=[]
		for i,replica in enumerate(self.replicas):
			t=Thread(
				name=f"Silhoete-{i}",
				target=PrimaryGeneric.silhoete_recv_handler,
				args=(self,replica)
			)
			sil_threads.append(t)
			t.start()
		#---------------------------------------------------------------------------------
		#start replicator sender threads
		replicator=Replicator(self.replicas,self.__BATCH_PAYID,self.total_batches)
		replicator.start()
		#feed replicator
		for i,chunk in enumerate(self.stream):
			batch=self.preproc(chunk.values)
			compressed=zlib.compress(batch.tobytes(),level=1)
			batch_shape=batch.shape
			replicator.add_job(batch_shape,compressed)
			del(batch)
		tmax=i
		
		replicator.join()
		
		self.send_to_all_replicas(PAYID.end)
		#---------------------------------------------------------------------------------
		#join recvs
		for t in sil_threads:
			t.join()
		#---------------------------------------------------------------------------------
		#determine winners and request labels
		if len(self.winners)!=tmax+1:
			logging.warning(f"Didn't recieve all t callbacks {len(self.winners),tmax+1}")
		winner_results=[]
		for t,winner in enumerate(self.winners.values()):
			print(f"requesting results for {winner.msock} on k={winner.k} and time={t}")
			winner.msock.send(Payload(PAYID.results_req,(t,winner.k)))
			result=winner.msock.recv(PAYID.compressed_float64_matrix).obj
			winner_results.append(result.tolist())
		self.send_to_all_replicas(PAYID.end)
		t=self.overall_timer.stop()
		#---------------------------------------------------------------------------------
		#save results
		print(f"saving results '{self.output}'")
		with CustomZipFile(self.output) as zf:
			#-----------------------------------------------------------------------------
			#log replicas extra info
			for i,replica in enumerate(self.replicas):
				result=replica.recv(PAYID.pickle).obj
				result["ip"]=replica.ip
				zf.add_json(f"replica{i}.json",result)
			#---------------------------------------------------------------------------------
			#log everything from primary
			zf.add_json("overall.json",dict(time=t,silhouette=winner.sil))
			zf.add_json("per_batch.json",self.bucket.to_dicts())
			zf.add_json("cluster_centers.json",winner_results)
			config_json=force_json(self)
			config_json.update(
				stream_fname=self.stream.fname.name,
				chunk_size=self.stream.chunk_size,
				stream_dtype=str(self.stream.dtype),
				output_fname=self.output.name,
				total_mem=virtual_memory().total,
				commit_hash=get_current_commit_hash()
			)
			zf.add_json("config.json",config_json,indent=4)