import os
from sklearn.cluster import KMeans
try:
	from .clustream import CluStream as CluStream_
except ImportError:
	backup=os.getcwd()
	print("compiling CluStream")
	os.chdir(os.path.join(os.path.dirname(__file__),"src"))
	os.system("make")
	os.chdir("..")
	try:
		from .clustream import CluStream as CluStream_
	except ImportError:
		raise ImportError("Something went wrong in the compilation")
	os.chdir(backup)

class CluStream(CluStream_):
	def init_offline(self,init_points,seed=0,n_init=3,max_iter=300):
		"""
		initialize microclusters using kmeans++

		Args:
			init_points (ndarray): points to initialize
			seed (int):random number generator seed 
			n_init (int): number of kmeans runs
			max_iter (int): max number of kmeans iterations
		"""
		cluster_centers=KMeans(
			n_clusters=self.m,
			init="k-means++",
			random_state=seed,
			n_init=n_init,
			max_iter=max_iter
		).fit(init_points).cluster_centers_
		self.init_kernels_offline(cluster_centers,init_points)

	def get_macro_clusters(self,k,seed=0,n_init=3,max_iter=300):
		"""
		clusters microclusters and returns macroclusters centers

		Args:
			k (int): number of centers
			seed (int): random number generator seed
			n_init (int): number of kmeans runs
			max_iter (int): max number of kmeans iterations
		"""
		return KMeans(
			init="k-means++",
	 		random_state=seed,
	 		n_clusters=k,
	 		n_init=n_init,
	 		max_iter=max_iter

	 	).fit(self.get_kernel_centers()).cluster_centers_