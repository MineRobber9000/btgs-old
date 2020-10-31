"""A simple echo server implemented as a subclass of btgs.server.Server."""
import os.path, time, sys, os, signal
from urllib.parse import unquote

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

class SubServer(Server):
	FILESYSTEM_BACKED=False
	def handle_cgi(self,path,parseresult):
		if path!="7f000001.nip.io/echo":
			self.write.write("51 Resource not found\r\n".encode("utf-8"))
			return
		if not parseresult.query:
			self.write.write("10 Input some text and I'll say it back to you:\r\n".encode("utf-8"))
			return
		self.write.write("20 text/plain\r\n{}".format(unquote(parseresult.query)).encode("utf-8"))

server = SubServer(('127.0.0.1',PORT),{"7f000001.nip.io":("localhost.crt","localhost.key")})
server.PREFIX = "./testroot"

def stop_server(*args):
	server.running=False
	raise SystemExit()
signal.signal(signal.SIGINT,stop_server)

server.start()
