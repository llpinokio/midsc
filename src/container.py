#!/usr/bin/env python3
from slave import Slave
from network import ServerSocket
import json

if __name__=="__main__":
	with open("config.json") as f:
		config=json.load(f)
	print("auxiliar server started",flush=True)
	server=ServerSocket(3523)
	master=server.accept()
	print(f"connected to {master.ip}",flush=True)
	import logging
	logging.basicConfig(format='[%(levelname)s]%(message)s',level=logging.DEBUG)
	Slave(**config).run(master)