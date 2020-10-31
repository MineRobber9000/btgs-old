import socket, ssl, os
from urllib.parse import urlparse
from btgs.mime import guess_mimetype

HOSTNAMES = dict()

def handle_sni(hostname_dict):
	def _handle(sock,hostname,ctx):
		if hostname in hostname_dict:
			sock.context=hostname_dict[hostname]
		return None
	return _handle

def create_context(certfile,keyfile=None,password=None,sni=lambda s, h, c: None):
	context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	context.options |= ssl.OP_NO_TLSv1
	context.options |= ssl.OP_NO_TLSv1_1
	context.verify_mode = ssl.CERT_OPTIONAL
	context.load_cert_chain(certfile,keyfile,password)
	return context

class Server:
	PREFIX = "/var/gemini"
	INDEXES = ["index.gmi",None]
	FILESYSTEM_BACKED = True
	def __init__(self,bind,hostnames={}):
		self.bind = bind
		self.hostnames = {}
		for hostname, args in hostnames.items():
			self.hostnames[hostname]=create_context(*args,sni=handle_sni(self.hostnames))
		self.start_context = next(iter(self.hostnames.values()))
	def start(self):
		self.running = True
		with socket.socket(socket.AF_INET,socket.SOCK_STREAM,0) as sock:
			sock.bind(self.bind)
			sock.listen(5)
			with self.start_context.wrap_socket(sock,True) as ssock:
				while self.running:
					conn, client_addr = ssock.accept()
					self.conn = conn
					self.read = conn.makefile('r',encoding="utf-8")
					self.write = conn.makefile('wb')
					url = self.read.readline().strip('\r\n')
					del self.read # that's literally all we need that for
					self.handle(urlparse(url))
					self.write.flush()
					self.conn.shutdown(socket.SHUT_RDWR)
					self.conn.close()
	def handle(self,parseresult):
		if parseresult.scheme!="gemini":
			return self.handle_nongemini(parseresult)
		if parseresult.hostname not in self.hostnames:
			# note that I don't check which hostname the user connected to
			# we'll proxy results within our server, but not outside of our server
			return self.handle_proxy(parseresult)
		return self.handle_gemini(parseresult)
	def handle_nongemini(self,parseresult):
		# The base server doesn't handle non-gemini requests.
		# But to make it easier to add that functionality in a subclass, we shell out the error function to here.
		self.write.write("53 Cowardly refusing to proxy {} request\r\n".format(parseresult.scheme).encode("utf-8"))
	def handle_proxy(self,parseresult):
		# The base server also doesn't handle proxy requests.
		# But to make it easier to add that functionality in a subclass, shell out the error function to here.
		self.write.write("53 Cowardly refusing to serve proxy request for resource on server {}".format(parseresult.hostname).encode("utf-8"))
	def handle_gemini(self,parseresult):
		path = self.get_path(parseresult)
		if self.FILESYSTEM_BACKED:
			path = os.path.join(self.PREFIX,self.get_path(parseresult))
			if not os.path.exists(path):
				self.write.write("51 File not found\r\n".encode("utf-8"))
				return
			if os.path.isdir(path):
				for index in self.INDEXES:
					if index is None:
						return self.handle_directory(path)
					if os.path.exists(os.path.join(path,index)):
						path = os.path.join(path,index)
						break
			if not os.access(path,os.R_OK):
				self.write.write("40 Resource unavailable\r\n".encode("utf-8"))
				return
		if self.handle_cgi(path,parseresult):
			return
		if self.FILESYSTEM_BACKED:
			with open(path,"rb") as f:
				content = f.read()
			mime_type = guess_mimetype(path,content)
			self.write.write("20 {}\r\n".format(mime_type).encode("utf-8"))
			self.write.write(content)
	def get_path(self,parseresult):
		return parseresult.hostname+parseresult.path
	def handle_directory(self,path):
		# The base server doesn't do directory listings.
		# In theory one could build a directory listing using text/gemini, but I don't want to do that.
		# To make it easier to add that functionality in a subclass/at a later date, I'll shell out the error to here.
		self.write.write("40 Resource unavailable\r\n".encode("utf-8"))
	def handle_cgi(self,path,parseresult):
		# I'm not sure how to handle CGI so I'm going to *start* by just not bothering.
		# Eventually I would like to implement some form of CGI though.
		# The goal is to return True if the file is CGI (and run the CGI in this method), or return False if the file
		# isn't CGI.
		return False
