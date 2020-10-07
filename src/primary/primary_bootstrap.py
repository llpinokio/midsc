import numpy as np
from utils import Timer,timeout
from network import Ship,ServerSocket,PAYID,Payload
from math import ceil

class PrimaryBootstrap:
	"""
	Args:
		algorithm (str): the algorithm to use
		output (str): zip output fname
		stream (core.Stream): Dataset stream
		number_nodes (int): total number of replica nodes to connect
		seed (int): seed to use in the replicas
		repetitions (int): number of times to repeat replica algorithm
		lower_threshold (int): lower threshold for kappas set generation
		kappas_method (function): kappas set builder function
		remote_nodes (str): path to the file that contains the ip for all remote replicas
	Attributes:
		stream (str):
		number_nodes (int):
		lower_threshold (int):
		kappas_method (function):
		kappas (ndarray):kappa set for each replica
		replicas (list): list of connected replicas
		ship (midsc.network.Ship): ship object containing the number of nodes necessary
		overall_timer (midsc.Timer): Timer object for overall runtime
		time_to_wait (int or None): time in seconds to wait for replicas
	"""
	def __init__(self,
			algorithm,
			output,
			stream,
			number_nodes,
			seed,
			repetitions,
			lower_threshold,
			kappas_method,
			remote_nodes,
			distance_matrix_method,
			time_to_wait
		):
		self.algorithm=algorithm
		self.output=output
		self.stream=stream
		self.number_nodes=number_nodes
		self.seed=seed
		self.repetitions=repetitions
		self.lower_threshold=lower_threshold
		self.kappas_method=kappas_method
		self.kappas=np.empty(0)
		self.distance_matrix_method=distance_matrix_method
		self.time_to_wait=time_to_wait

		self.total_batches=ceil(self.stream.lines/self.stream.chunk_size)
		self.replicas=set()
		#t -> msock
		self.ship=Ship(self.number_nodes,remote_nodes)
		self.overall_timer=Timer()
	
	def accept_handler(self,msock):
		"""
		Helper method to accept some socket based on the protocol.
		adds msock to replicas list
		
		Args:
			msock (network.Socket): socket to be added.
		"""
		if self.number_nodes!=None and len(self.replicas)==self.number_nodes:
			print(f"ignoring {msock.ip} because its too much replicas than expected")
			msock.send(Payload(PAYID.err))
			return
		self.replicas.add(msock)
		print(f"replica {msock.ip} connected")

	def send_to_all_replicas(self,payid,*args):
		for replica in self.replicas:
			replica.send(Payload(payid,*args))

	def __check_replicas_connected(self):
		if self.number_nodes==None:return
		got,expected=len(self.replicas),self.number_nodes
		if got==expected:return

		if got>expected:
			raise RuntimeError(f"too much nodes connected, {got-expected} more than expected")
		else:
			raise RuntimeError(f"not enough nodes connected, remained {expected-got} to connect")

	def __connect_local_nodes(self):
		server=ServerSocket(3523)
		if self.time_to_wait==None:
			print("waiting for replicas, press [CTRL+C] to stop waiting")
			try:
				while True:
					self.accept_handler(server.accept()) #no nedd to be multithread
			except KeyboardInterrupt:
				pass
		else:
			print(f"waiting for replicas for {self.time_to_wait} seconds")
			with timeout(self.time_to_wait):
				while True:
					self.accept_handler(server.accept())
		self.__check_replicas_connected()
		if len(self.replicas)==0:
			raise RuntimeError("no replicas connected")

	def run(self,**json_opts):
		"""
		Run primary's node initialization and send extra json_opts to replicas

		Args:
			**json_opts : extra json options to send to replicas 
		"""
		if self.ship.ips!=[]:
			#connect remote nodes
			for msock in self.ship.get_node_sockets():
				self.accept_handler(msock)
			self.__check_replicas_connected()
		else:
			self.__connect_local_nodes()
		
		self.kappas=self.kappas_method(len(self.replicas),self.lower_threshold)
		for replica,kappa in zip(self.replicas,self.kappas):
			replica.send(Payload(PAYID.pickle,{**{
				"algorithm":self.algorithm,
				"kappa":kappa,
				"seed":self.seed,
				"repetitions":self.repetitions,
				"distance_matrix_method":self.distance_matrix_method,
				"batch_size":self.batch_size
			},**json_opts}))

	def __del__(self):
		print("closing everything")
		for replica in self.replicas:
			replica.close()