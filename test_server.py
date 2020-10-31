"""A simple test server running a localhost-only instance of Big Tiddy Gemini Server."""
import os.path, time, sys, os, signal

PORT = 1965

if "PORT" in os.environ: PORT = int(os.environ["PORT"])

ONE_YEAR_IN_SECONDS = 365*24*60*60

if (not os.path.exists("localhost.key")) or (time.time()-os.path.getmtime("localhost.key"))>ONE_YEAR_IN_SECONDS:
	print("#####################################################")
	print("# ERROR: Your key is either missing or out of date! #")
	print("# The test server expects a certificate and private #")
	print("# key (created/modified less than 365 days ago) in  #")
	print("# localhost.crt and localhost.key respectively. If  #")
	print("# you don't have a cert, run `gen_cert.sh` and one  #")
	print("# will be generated for you.                        #")
	print("#####################################################")
	sys.exit(1)

from btgs.server import Server

server = Server(('127.0.0.1',PORT),{"7f000001.nip.io":("localhost.crt","localhost.key")})
server.PREFIX = "./testroot"

def stop_server(*args):
	server.running=False
	raise SystemExit()
signal.signal(signal.SIGINT,stop_server)

server.start()
