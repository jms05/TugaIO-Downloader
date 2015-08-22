import os

def getMoviename(url):
	name = "null"
	filemane = "tuga.io/filme/" + url.split("/")[len(url.split("/"))-1]
	os.system("wget -U firefox -r -np " + url)
	f = open(filemane ,'r')
	for line in f:
		if  "itemprop=\"name\"" in line:
			fracs = line.split("<")
			for frac in fracs:
				if "\"t\"" in frac:
					name= frac.split(">")[len(frac.split(">"))-1].strip() 
				if "\"y\"" in frac:
					ano = frac.split(">")[len(frac.split(">"))-1].strip()
					name = name +" "+ ano
	f.close()
	os.system("rm -rf tuga.io")
	return name

def getPoster(url):
	poster = "null"
	filemane = "tuga.io/filme/" + url.split("/")[len(url.split("/"))-1]
	os.system("wget -U firefox -r -np " + url)
	f = open(filemane ,'r')
	for line in f:
		if  "posters" in line:
			fracs = line.split("\"")
			for frac in fracs:
				if "posters" in frac:
					poster = frac.split("/")[len(frac.split("/"))-1]
					break
	f.close()
	os.system("rm -rf tuga.io")
	return poster

def getSubs(url):
	sub = "null"
	filemane = "tuga.io/filme/" + url.split("/")[len(url.split("/"))-1]
	os.system("wget -U firefox -r -np " + url)
	f = open(filemane ,'r')
	for line in f:
		if  "subtitles" in line:
			fracs = line.split("\"")
			for frac in fracs:
				if "subtitles" in frac:
					sub = frac.split("/")[len(frac.split("/"))-1]
					break
	f.close()
	os.system("rm -rf tuga.io")
	return sub

def getMovieURl(url):
	movie = "null"
	filemane = "tuga.io/filme/" + url.split("/")[len(url.split("/"))-1]
	os.system("wget -U firefox -r -np " + url)
	f = open(filemane ,'r')
	for line in f:
		if  "file" in line and "http" in line:
			fracs = line.split("\'")
			for frac in fracs:
				if "http" in frac:
					movie = frac
					break
	f.close()
	os.system("rm -rf tuga.io")
	return movie

class TugaIo:
	""" ULRL's contains the movie data"""
	basePoster = "http://tuga.io/posters/"
	baseSubs = "http://tuga.io/subtitles/"

	def __init__(self, movieURL):
		self.movieurl = getMovieURl(movieURL)
		self.moviename = getMoviename(movieURL)
		self.movieposter = TugaIo.basePoster + getPoster(movieURL)
		self.movieSubs = TugaIo.baseSubs + getSubs(movieURL)

##Ver para por os nomes bonitos
	def download(self,path):
		print("mkdir \"" + self.moviename+"\"")
		subsname = self.movieSubs.split("/")[len(self.movieSubs.split("/"))-1]
		print("curl -O " + self.movieSubs)
		print("mv " +  subsname +" "+ self.moviename)
		postername = self.movieposter.split("/")[len(self.movieposter.split("/"))-1]
		print("wget " + self.movieposter)
		print("mv " + postername +" "+ self.moviename)
		movien = self.movieurl.split("/")[len(self.movieurl.split("/"))-1]
		print("wget " + self.movieurl)
		print("mv " +  movien +" "+ self.moviename)
		print("mv " + self.moviename + " "+ path)

m = TugaIo("http://tuga.io/filme/tt0172495")

print "Url:  " +m.movieurl
print "Name:   " + m.moviename
print "Poster:   " + m.movieposter
print "Sub:   " + m.movieSubs

m.download("teste")


"""
	def downloadMovie(self,path):
		os.system("mkdir " + self.moviename)
		subsname = self.movieSubs.split("/").[len(self.movieSubs.split("/"))-1]
		os.system("curl -O " + self.movieSubs)
		os.system("mv " subsname +" "+ self.moviename)
		postername = self.movieposter.split("/").[len(self.movieposter.split("/"))-1]
		os.system("wget " + self.movieposter)
		os.system("mv " postername +" "+ self.moviename)
		movien = self.movieurl.split("/").[len(self.movieurl.split("/"))-1]
		os.system("wget " + self.movieurl)
		os.system("mv " movien +" "+ self.moviename)
"""
