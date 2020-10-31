import mimetypes
mimetypes.init()
mimetypes.add_type("text/gemini",".gmi")
mimetypes.add_type("text/gemini",".gemini")

def guess_mimetype(filename,content=b''):
	return mimetypes.guess_type(filename,False)[0]
