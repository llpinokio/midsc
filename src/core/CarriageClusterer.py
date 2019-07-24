import numpy as np
from sklearn.cluster import MiniBatchKMeans as ClustererAlgo
# from sklearn.cluster import Birch as ClustererAlgo
from sklearn.metrics import silhouette_score
from .Cache import Cache
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
from math import sqrt,ceil
#drawer clusterer
class CarriageClusterer:
	def __add_shelve(self,k):
		c=CarriageShelve(k,self.batch_size)
		self.drawer.append(c)

	def __init__(self,kc,kci,batch_size=None):
		self.kc=kc
		self.kci=kci
		self.batch_size=batch_size
		self.datapoints=Cache(np.float32)
		self.pool=Pool(cpu_count())
		self.drawer=[]
		self.__add_shelve(self.kc)
	def __handler(arg):
		self,clusterer,batch=arg
		clusterer.add(batch)
		return clusterer.k,clusterer.get_score(self.datapoints.ndarray)
	def add_and_get_score(self,batch):
		maxn=ceil(sqrt(self.datapoints.size+len(batch)))
		# print(f"for k in range({self.drawer[-1].k+self.kci},{maxn+1},{self.kci}):")
		for k in range(self.drawer[-1].k+self.kci,maxn+1,self.kci):
			# print(f"[KMEANS] CREATING k={k}")
			self.__add_shelve(k)
		self.datapoints.add(batch)
		return self.pool.imap_unordered(CarriageClusterer.__handler,((self,c,self.datapoints.ndarray,) for c in self.drawer))

class CarriageShelve:
	def __init__(self,k,batch_size=None):
		self.k=k
		self.clusterer=ClustererAlgo(
			n_clusters=k,
			# batch_size=batch_size
			)
		self.labels=np.empty(0)
	def add(self,datapoints):
		self.clusterer.fit(datapoints)
		self.labels=self.clusterer.labels_
	def get_score(self,datapoints):
		return silhouette_score(datapoints,self.clusterer.labels_)
