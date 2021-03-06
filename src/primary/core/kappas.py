import numpy as np
from math import ceil

def get_kappas_gauss(no_replicas,l):
	"""
	Returns kappas set with gauss's trick for each replica,
	so that each kappa set have the same sum and mean

	Args:
		no_replicas (int): number of replicas
		l (int): lower threshold of the number of columns of the kappa matrix
	Returns:
		list
	"""
	#l must be even and divisble by l
	#adds with the ceil of the division, so that l is divisible by no_replicas
	total=no_replicas*ceil(l/no_replicas)
	#gauss's trick only works with even numbers, so
	if (total//no_replicas)%2==1:
		total+=no_replicas
	unordered_kappas=list(range(2,total+2))
	m=no_replicas
	n=total//no_replicas
	return np.array(rearange(unordered_kappas)).reshape((m,n)).tolist()
def rearange(L): # reorders list of k's to do the gauss's trick
	
	n=len(L)
	first_half=L[0:n//2] #divides list from start to half
	second_half=L[:n//2 -1:-1] #divides list from half to end and inverts it
	
	ans=[]
	while first_half or second_half: #intercalate the lists
		if first_half:
			ans.append(first_half.pop(0))
		if second_half:
			ans.append(second_half.pop(0))
	return ans
def get_kappas_v1(no_replicas,l):
	"""
	Returns kappas set with the transpose matrix method with empty elements

	Args:
		no_replicas (int): number of replicas
		l (int): lower threshold of the number of columns of the kappa matrix
	Returns:
		list
	"""
	kappa=lambda i:[k for k in range(2+i,l+1,no_replicas)]
	return [kappa(i) for i in range(no_replicas)]
def get_kappas_v2(no_replicas,l):
	"""
	Returns kappas set with the matrix method without empty elements,
	so that each kappa set have the same deviation

	Args:
		no_replicas (int): number of replicas
		l (int): lower threshold of the number of columns of the kappa matrix
	Returns:
		list
	"""
	total=no_replicas*ceil(l/no_replicas)
	m=total//no_replicas
	n=no_replicas
	kappas=np.array(range(2,total+2)).reshape((m,n)).T
	return kappas.tolist()
def get_kappas_random(no_replicas,l):
	np.random.seed(1)
	total=no_replicas*ceil(l/no_replicas)
	kappas=np.array(range(2,total+2))
	np.random.shuffle(kappas)
	m=no_replicas
	n=total//no_replicas
	return kappas.reshape((m,n)).tolist()