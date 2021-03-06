from . import ClientSocket
from pathlib import Path

class Ship:
	"""
	Helper class to read remote_nodes.txt file and connect to
	
	Args:
		n (str): Number of nodes to use
		tries (int): maximum number of tries
	"""
	def __init__(self,n,remote_nodes,tries=15):
		self.n=n
		self.tries=tries
		self.ips=[]
		if remote_nodes==None:return
		file_handler=Path(remote_nodes)
		if not file_handler.exists():return
		self.ips=file_handler.read_text().strip().split("\n")[:self.n]
		
	def get_node_sockets(self):
		"""
		return sockets of necessary nodes
		
		Yields:
			midsc.network.Socket instance
		"""

		for ip in self.ips:
			ans=None
			for i in range(self.tries):
				print(f"trying to connect to {ip}:3523 ({i+1})")
				ans=ClientSocket(ip,3523)
				break
			assert ans!=None,f"Error connecting to {ip}"
			yield ans
