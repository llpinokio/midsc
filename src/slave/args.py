from argparse import ArgumentParser
import logging
def get_args():
	parser=ArgumentParser()
	parser.add_argument(
		"master_addr",
		help="address of the master"
	)
	parser.add_argument(
		'-v',
		'--verbose',
		action='store_true',
		help="enable verbose"
	)
	parser.add_argument(
		'-s',
		'--server-mode',
		action='store_true',
		help="starts as a server, so that the master starts the connection"
	)
	parser.add_argument(
		'-g',
		'--ghost',
		type=int,
		help="enable ghost mode in batch index TIME",
		metavar="TIME"
	)
	parser.add_argument(
		'-c',
		'--disk-cache',
		type=int,
		help="use disk cache, keeping max of BATCHES in memory",
		metavar="BATCHES"
	)
	
	args=parser.parse_args()
	if args.verbose:
		logging.basicConfig(format='[%(levelname)s]%(message)s',level=logging.DEBUG)
	return args