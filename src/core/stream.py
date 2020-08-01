from pandas import read_csv
from subprocess import check_output
from itertools import chain

import numpy as np
def __count_flines(fname):
	try:
		#try to use wc -l
		return int(check_output(["wc","-l",fname]).decode().split(" ")[0])
	except FileNotFoundError:
		pass
	ans=0
	with open(fname) as f:
		while True:
			block=f.read(4000)
			if not block:
				break
			ans+=block.count("\n")
	return ans

class Stream:
	def __init__(self,fname,chunksize,dtype=np.float64):
		"""
		class to generate a stream from a csv file, providing info about it's shape and 
		peek/pop() functions

		Args:
			fname (str): path to csv file
			chunksize (int): length of chunks to split the dataset
			dtype : datatype for each chunk

		"""
		self.fname=fname
		self.chunksize=chunksize
		self.lines=__count_flines(self.fname)
		with open(fname) as f:self.columns=next(f).count(",")+1
		self.stream=read_csv(fname,chunksize=chunksize,header=None,dtype=dtype)
		self.__peek=None

	def peek(self):
		assert(self.__peek==None)
		self.__peek=next(self.stream)
		return self.__peek

	def pop(self):
		return next(self.stream)

	def __iter__(self):
		extra=[] if self.__peek==None else [self.__peek]
		return chain(extra,self.stream)
			
