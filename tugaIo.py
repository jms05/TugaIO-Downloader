import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

from net import Net
from bs4 import BeautifulSoup
import re
import urllib2
import urllib
import urlparse
import cookielib
import re
import time

##fim kodi addon

from xml.dom import minidom
from unicodedata import normalize
import cfscrape
import wget
import shutil
import codecs



#libs = []
libs = ["/mnt/Multimedia_NV/","/mnt/Anime/Filmes/","/mnt/Filmes/"]
plexserver = "192.168.1.71"
finalpath = True
finalpathloc =  "/mnt/Filmes/Filmes"
filepath = "movieList.txt"
deleteonError = True
plexUpdate = True

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:40.0) Gecko/20100101 Firefox/40.0'
cf_cookie_file = os.path.join(os.path.dirname(__file__), 'tugaio.cache')

net = Net()
net.set_cookies(cf_cookie_file)
net.set_user_agent(user_agent)

#####Codigo Addon Kodi

def cf_decrypt_ddos(url, agent, cookie_file):
    class NoRedirection(urllib2.HTTPErrorProcessor):
        def http_response(self, request, response):
            return response

    if len(agent) == 0:
        agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'

    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(NoRedirection, urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', agent)]
    response = opener.open(url)

    try:
        set_cookie = str(response.headers.get('Set-Cookie'))
    except:
        set_cookie = ''

    print ['Set-Cookie', set_cookie]

    responce_html = response.read()

    js_header = '<link rel="shortcut icon" href="/Content/images/favicon.ico" type="image/x-icon" /><script type="text/javascript">'
    if js_header in responce_html:
        responce_html = responce_html.split(js_header)[-1]

    jschl = re.compile('name="jschl_vc" value="(.+?)"/>').findall(responce_html)[0]
    print ['jschl', jschl]

    try:
        cf_pass = re.compile('name="pass" value="(.+?)"/>').findall(responce_html)[0]
    except:
        cf_pass = ''

    print ['cf_pass', cf_pass]

    try:
        cf_challenge_form = \
            re.compile('<form id="challenge-form" action="(/[^"]+)" method="\D+">').findall(responce_html)[0]
    except:
        cf_challenge_form = '/cdn-cgi/l/chk_jschl'

    print ['cf_challenge_form', cf_challenge_form]

    init = re.compile(
        'setTimeout\(function\(\){\s*\n*\s*(?:var \D,\D,\D,\D, [0-9A-Za-z]+={"[0-9A-Za-z]+"|.*?.*):(.*?)};').findall(
        responce_html)[-1]
    print ['init', init]

    builder = re.compile(r"challenge-form\'\);\s*\n*\r*\a*\s*(.*)a.v").findall(responce_html)[0]
    print ['builder', builder]

    try:
        wait_time = int(re.compile(r"f.submit\(\);\s*\n*\s*},\s*(\d+)\)").findall(responce_html)[-1])
    except:
        wait_time = 5000

    print ['wait_time', wait_time]

    decrypt_value = cf_evaluate_js_string(init)
    print ['value_to_decrypt', decrypt_value]

    lines = builder.split(';')
    for line in lines:
        if len(line) > 0 and '=' in line:
            try:
                sections = line.split('=')
                line_val = cf_evaluate_js_string(sections[1])
                decrypt_value = int(eval(str(decrypt_value) + sections[0][-1] + str(line_val)))
            except:
                pass

    print ['decrypted_value', decrypt_value]

    hostname = get_domain_from_url(url)
    base_url = "http://" + hostname
    print ['base_url', base_url]
    print ['hostname', hostname, len(hostname)]

    answer = decrypt_value + len(hostname)
    print ['answer', answer]

    if cf_pass == '':
        query = '%s%s?jschl_vc=%s&jschl_answer=%s' % (str(base_url), str(cf_challenge_form), str(jschl), str(answer))
    else:
        query = '%s%s?jschl_vc=%s&pass=%s&jschl_answer=%s' % (
            str(base_url), str(cf_challenge_form), str(jschl), str(cf_pass), str(answer))
    print ['query', query]

    sleep(wait_time)

    opener = urllib2.build_opener(NoRedirection, urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', agent)]
    response = opener.open(query)
    cookie = str(response.headers.get('Set-Cookie'))
    print ['Set-Cookie', cookie]

    cj = cookielib.LWPCookieJar(cookie_file)
    cj.clear()
    request = urllib2.Request(url)
    cj.extract_cookies(response, request)
    response.close()

    final_response = opener.open(request)
    if final_response.code == 200:
        cj.save(cookie_file)
        return True

    return False

def cf_generate_new_cookie(url, user_agent, cookie_file):
    retries = 10
    while retries > 0 and not cf_decrypt_ddos(url, user_agent, cookie_file):

        sleep(1)
        retries -= 1

    return retries > 0

def is_cookie_expired(url, net):
    domain = "." + get_domain_from_url(url)
    print domain
    for cookie in net._cj:
        if cookie.domain == domain:
            return cookie.is_expired()

    return True

def create_request(url, headers={}, data=None):
    try:
        return net.http_GET(url, headers=headers).content

    except:
        # Possible Cloudflare DDOS Protection
        net._cj.clear()
        #net.set_cookies(cf_cookie_file)

        #if is_cookie_expired(url, net):
        print "cookie_expired"
        cf_generate_new_cookie(url, user_agent, cf_cookie_file)
        net.set_cookies(cf_cookie_file)
        net.set_user_agent(user_agent)
        response = net.http_GET(url, headers=headers)
        net.save_cookies(cf_cookie_file)
        return response.content

def myfunc(s):
	ret = []
	saux = s.split("\\")
	for char in saux:
		v = hex(char)
		ret.append(v)
	return ret

def resolve_video_and_subtitles_url(base_url, path):
    title_html = create_request(base_url + path)
    query = BeautifulSoup(title_html, "html.parser")
    lines = []
    video_url=None
    subtitles_url =None
    query_data = query("script", {"src": re.compile("php")})
    # php_link = ""
    # if (len(query_data) == 0):
    #     php_link = query("script", {"data-rocketsrc": re.compile("php")})[0].attrs["data-rocketsrc"]
    # else:
    php_link = query_data[0].attrs["src"]

    if base_url not in php_link:
        php_link = base_url + php_link
    player_data = create_request(php_link, {'Referer': base_url + path})
    #print "pdata"
    #print player_data
    mc = (player_data.split("\n")[0]).split("\"")[1]
    #print "mc"
    #print mc
    btys = mc.split("\\")
    link = ""
    arr = []
    for bt in btys:
    	tmp =bt.replace("x","").encode("ascii", "ignore")
    	if tmp!="":
    		arr.append(int("0x"+tmp, 0))
    		link = link + chr(int("0x"+tmp, 0))

    for s in player_data.split(","):

        lines.append(s.split("{")[-1])

    for line in lines:
        if "file" in line and "http" in line:
            video_url=line.split("\"")[-2]
        if "file" in line and "srt" in line:
            subtitles_url=line.split("\'")[-2]


    #print str(video_url)
    if not video_url:
    	video_url = link
    #print str(video_url)
    #raw_input()
    return {"video": video_url, "subtitles": subtitles_url}


###### Fim Codigo Addon Kodi
def purge(dir, pattern):
    for f in os.listdir(dir):
    	if re.search(pattern, f):
    		os.remove(os.path.join(dir, f))

def download(url,save=True,prnt=True):
	if prnt:
		print "Passing Cloufrare browser validation!!!"
		print "Please wait "
	scraper = cfscrape.create_scraper()
	if save:
		name = url.split("/")[-1]
		fs = open(name,"wb")
		fs.write(scraper.get(url).content)
		fs.close()
		return name
	else: return (scraper.get(url).content).split("\n")

def remover_acentos(txt, codif='utf-8'):
    return normalize('NFKD', txt.decode(codif)).encode('ASCII','ignore')

def strClear(string):
	final = ""
	for char in string:
		if (char>="a" and char<="z") or (char>="A" and char<="Z") or (char>="0" and char<="9"):
			final+=char
	return final

def binary_search_String(value=None,lista=[]): #need a sorted list
	if not value or not lista: return False
	lo=0
	hi = len(lista)
	val=strClear(remover_acentos(value)).lower()
	while lo < hi:
		mid = (lo+hi)//2
		midval = strClear(remover_acentos(lista[mid])).lower()
		if midval < val:
			lo = mid+1
		elif midval > val:
			hi = mid
		else:
			return True
	return False

def getFilmes(libs=[]):
	dic =[]
	filmes = []
	for x in range(ord('a'),ord('z')+1):
		dic.append(chr(x))

	for lib in libs:
		for dirname, dirnames, filenames in os.walk(lib):
			for subdirname in dirnames:
				movname=strClear(remover_acentos(os.path.join(dirname, subdirname).split(os.sep)[-1].split("(")[0].replace(" ",""))).lower()
				if not binary_search_String(movname,dic):
					filmes.append(movname)
	return sorted(filmes)
	
def getfinaldir(name):
	ignoredwords =["the","a","o","as","os","an"]
	words = name.strip().split()
	if words[0].lower() in ignoredwords:
		word= words[1]
	else:
		word = words[0]
	letra = word.upper()[0]
	if letra.isdigit():return "/0-9/" 
	return "/" + word.upper()[0] +"/"

def plexforceupdate(host = "localhost" , source_type = ['movie']): # Valid values: artist (for music), movie, show (for tv)
	base_url = 'http://%s:32400/library/sections' % host
	refresh_url = '%s/%%s/refresh?force=1' % base_url
	try:
		xml_sections = minidom.parse(urllib.urlopen(base_url))
		sections = xml_sections.getElementsByTagName('Directory')
		for s in sections:
			if s.getAttribute('type') in source_type:
				url = refresh_url % s.getAttribute('key')
				x = urllib.urlopen(url)
	except:
		raise Exception("ERROR UPDATING PLEX MEDIA SERVER: " + host +":\n\t library:" + srt(source_type))

def removeBlocked(name):
	blockChars = ["<",">",":","\"","/","\\","|","?","*","\<","\>","\:","\/","\|","\?","\*","/<","/>","/:","/\"","//","/\\","/|","/?","/*"]
	ret = name
	for char in blockChars:
		ret = ret.replace(char,"")
		
	return ' '.join(ret.split())

def valid(url):
	if "http://tuga.io/filme/" in url: return True
	else: return False

def allinfo(array):
	for elem in array:
		if not elem : return False
	return True

def getElems2(url):
	#retArray[0] #movieName
	#retArray[1]  #movieURL
	#retArray[2]  #moviePoster
	#retArray[3]  #movieSubs
	#retArray[3]  #background
	retArray = []
	for x in range(0, 5):
		retArray.append(None)

	try:
		print "Getting Info From: " + url
		name = download(url,True)
		f = open(name,"r")
	except Exception as e:
		raise Exception("ERROR download: " + url + "\n Details: " + e.message)

	move = re.compile(r'file: "(.+?\.mp4)"')
	video_url = move.findall (f.read()) [0]
	print (video_url)
	name


	var = raw_input()
	if not allinfo(retArray):
		raise Exception("INFO ARRAY isn't valid " + str(retArray))

	f.close()
	os.remove(name)
	return retArray

def getElems(url):
	base_url="http://tuga.io/"
	#retArray[0] #movieName
	#retArray[1]  #movieURL
	#retArray[2]  #moviePoster
	#retArray[3]  #movieSubs
	#retArray[3]  #background
	pageinfo = None
	retArray = []
	for x in range(0, 5):
		retArray.append(None)

	try:
		print "Getting Info From: " + url
		f = download(url,False)
	except Exception as e:
		raise Exception("ERROR download: " + url + "\n Details: " + e.message)
	for line in f:
		if  "class=\"title\"><span" in line:
			fracs = line.split("<")
			for frac in fracs:
				if "\"t\"" in frac:
					name= frac.split(">")[-1].strip() 
				if "\"y\"" in frac:
					ano = frac.split(">")[-1].strip()
					retArray[0] = name +" "+ ano
					if allinfo(retArray): break

		if  "posters" in line:
			fracs = line.split("\"")
			for frac in fracs:
				if "posters" in frac:
					retArray[2] = frac.split("/")[-1]
					if allinfo(retArray): break

		if  "subtitles" in line:
			fracs = line.split("\"")
			for frac in fracs:
				if "subtitles" in frac:
					retArray[3] = frac.split("/")[-1]
					if allinfo(retArray): break

		if  "file" in line and "http" in line:
			fracs = line.split("\"")
			for frac in fracs:
				if "http" in frac:
					retArray[1] = frac
					if allinfo(retArray): break
		if "headers" in line:
			fracs= line.split("\'")
			for frac in fracs:
				if"headers" in frac:
					retArray[4]=frac.split("/")[-1]
					if allinfo(retArray): break
		if "player_data" in line:
			pageinfo= TugaIo.baseurl + line.split("\"")[-2].strip()

		#retArray[3] = url.split("/")[-1]+".srt"
		#retArray[1] = "movieurl"

	if not allinfo(retArray):
		path = url.split("tuga.io/")[-1].strip()
		#print "Path: " + path + "Base: " +  base_url
		phpfile = resolve_video_and_subtitles_url(base_url,path)
		#print str(phpfile)
		#raw_input()
		retArray[1] = phpfile["video"]
		aux = phpfile["subtitles"]
		retArray[3]=(phpfile["subtitles"].split("/"))[-1]
		#if "http://tuga.io/" in aux:
		#	retArray[3]=aux
		#else:
		#	retArray[3] = (base_url + phpfile["subtitles"]).replace("io//","io/").strip()
	if not allinfo(retArray):
		raise Exception("INFO ARRAY isn't valid " + str(retArray))

	return retArray

def getIMDBNames(imdbid=None):
	if not imdbid: return None
	url = "http://www.imdb.com/title/" + imdbid + "/releaseinfo"
	scraper = cfscrape.create_scraper()
	html = (scraper.get(url).content).split("\n")
	inaka= False
	ok = True
	contry= []
	names = []
	for line in range(0,len(html)): 
		if "<h4 class=\"li_group\">Also Known As (AKA)&nbsp;</h4>" in html[line]:
			inaka = True
		if inaka and "It looks like we don't have any AKAs" in html[line]:
			return None
		if inaka and "</table>" in html[line]:
			break
		if inaka:
			if "<td>" in html[line]:
				if ok: 
					ok=False
					l1 = remover_acentos(html[line].strip().split(">")[1].split("<")[0].strip())
					l2 = html[line+1].strip().split(">")[1].split("<")[0].strip()
					if l1 == "(original title)":
						contry.append("Original")
					else:
						contry.append(l1.split()[0])
					if len(remover_acentos(l2).strip())<len(l2.strip())-3:
						l2=None
					names.append(l2)
				else: ok = True

	ret = dict(zip(contry, names))

	if ret:
		return ret
	else:
		return None

def intersect(lista=None,dic=None):
		if not lista or not dic: return None
		for k in dic:
			if dic[k] != None:
				if binary_search_String((dic[k].split("(")[0].replace(" ","")),filmes): return (dic[k] + " ("+k+")")
		return None

def getYearIMDB(imdbid = None):

	if not imdbid: return None
	ano = None
	url = "http://www.imdb.com/title/" + imdbid
	scraper = cfscrape.create_scraper()
	html = (scraper.get(url).content).split("\n")
	for line in range(0,len(html)):
		if " <script>(function(t){ (t.events = t.events || {})[\"csm_head_pre_title\"] = new Date().getTime(); })(IMDbTimer);</script>" in html[line]:
			ano = html[line+1].strip().split()[-3]
			break
	return ano

class TugaIo:
	""" ULRL's contains the movie data"""
	basePoster = "http://tuga.io/posters/"
	baseSubs = "http://tuga.io/subtitles/"
	baseback = "http://tuga.io/headers/"
	baseurl="http://www.tuga.io"
	paralesdownloads=1
	activedownloads = 0
	def __init__(self, movieURL):
		#retArray[0] #movieName
		#retArray[1]  #movieURL
		#retArray[2]  #moviePoster
		#retArray[3]  #movieSubs
		infoArray = getElems(movieURL)
		try:
			imdbdic = getIMDBNames(movieURL.split("/")[-1])
		except:
			imdbdic = None
		self.alias = imdbdic
		self.tugaurl = movieURL.strip()
		self.movieurl = infoArray[1].strip()
		self.backgrund = TugaIo.baseback + infoArray[4].strip()
		try:
			self.moviename = removeBlocked(imdbdic["Original"] + " "+getYearIMDB(movieURL.split("/")[-1]))
			if not self.moviename:
				self.moviename = removeBlocked(infoArray[0]).strip()
		except:
			self.moviename = removeBlocked(infoArray[0]).strip()
		self.moviename = remover_acentos(self.moviename)
		self.movieposter = (TugaIo.basePoster + infoArray[2]).strip()
		self.movieSubs = (TugaIo.baseSubs + infoArray[3]).strip()

	def download(self,path,log,finaldir=False,deleteonErro=True):
			print "\033[1m\033[34mName: " + self.moviename + ":\033[0m "
			print "\t\033[1m\033[34mTuga Url: " + self.tugaurl + ";\033[0m "
			print "\t\033[1m\033[34mUrl: " +self.movieurl + ";\033[0m "
			print "\t\033[1m\033[34mPoster: " + self.movieposter + ";\033[0m "
			print "\t\033[1m\033[34mSub: " + self.movieSubs +";\033[0m "
			print "\t\033[1m\033[34mBackground: " + self.backgrund +";\033[0m "
			print "\t\033[1m\033[34mAlias: ",
			if self.alias:
				for k in self.alias:
					print str(self.alias[k])+ ", ",
			else: print  "None; ",
			print ";\033[0m "
			print "\033[5mMovie Is Downloading Please Wait!!!\033[0m"
			mkdir = True
			try:
				os.mkdir(self.moviename)
			except:
				log.write("WARNING: " + self.moviename + "\n")
				log.write("\tCANNOT CREAT DIR:" + self.moviename + "\n\t(The Download will continue the files will be stored on : " + os.getcwd().strip() + " )\n")
				log.write("------------------------------------\n")
				mkdir=False
			subsname = self.movieSubs.split("/")[-1]
			subs=True 
			try:
				print "Downloading subtitles!!!"
				download(self.movieSubs)
				print "Subtitles Downloaded"
			except:
				log.write("WARNING: " + self.moviename + "\n")
				log.write("\tCANNOT DOWNLOAD SUBTITLES:" + self.movieSubs + "\n")
				log.write("------------------------------------\n")
				subs = False
			if mkdir and subs:
				subext="."+subsname.split(".")[-1]
				shutil.move(subsname,self.moviename+os.sep+self.moviename+subext)
			backname = self.backgrund.split("/")[-1]
			back=True
			try:
				print "Downloading backgroud!!!"
				download(self.backgrund)
				print "Backgroud Downloaded"
			except:
				back=False
				log.write("WARNING: " + self.moviename + "\n")
				log.write("\tCANNOT DOWNLOAD BACKGROUD:" + self.movieposter + "\n")
				log.write("------------------------------------\n")
			if mkdir and back:
				backtext = "."+backname.split(".")[-1]
				shutil.move(backname,self.moviename+os.sep+"backgrund"+backtext)
			postername = self.movieposter.split("/")[-1]
			post=True
			try: 
				print "Downloading poster!!!"
				download(self.movieposter)
				print "Poster Downloaded"
			except:
				post=False
				log.write("WARNING: " + self.moviename + "\n")
				log.write("\tCANNOT DOWNLOAD POSTER:" + self.movieposter + "\n")
				log.write("------------------------------------\n")
			if mkdir and post:
				postext ="."+ postername.split(".")[-1]
				shutil.copyfile(postername,self.moviename+os.sep+"folder"+postext)
				shutil.move(postername,self.moviename+os.sep+self.moviename+postext)
			movien = self.movieurl.split("/")[-1]
			#Possivelmente usar a biblioteca wget do python (mas nao ha como saber se deu erro)
			if 0!= os.system("wget -c \"" + self.movieurl+"\""):
				if deleteonErro:
					shutil.rmtree(self.moviename)
				raise Exception("Download error on:" + self.movieurl )
			if mkdir:
				movext = "."+ self.movieurl.split(".")[-1]
				shutil.move(movien,self.moviename+os.sep+self.moviename+movext)
				if 0!= os.system("chmod 777 -R \"" +self.moviename +"\""):
					log.write("WARNING: " + self.moviename + "\n")
					log.write("\tCANNOT CHANGE PERMISSIONS: " + "chmod 777 -R \"" +self.moviename +"\"" + "\n")
					log.write("\t(Check your permissions)\n")
					log.write("------------------------------------\n")
				if path:
					if finaldir:
						path += getfinaldir(self.moviename) ##Para mover para a pasta da letra 
						path=path.replace("//","/")
					try:
						shutil.move(self.moviename,path)
						print "Movie Downloaded to " + path
					except:
						raise Exception("ERROR on command:\n\tmv \""  + self.moviename + "\" \""+ path + "\"\n(MOVIE DOWNLOADED TO:"+ os.getcwd().strip()+" )")
	
				else:
					print "Movie Downloaded to current dir"


def commented(line,mark="#"):
	return mark==line[0]
filepath = "movieList.txt"
try:
	filestream = open(filepath,"r")
except:
	print "an error occurred opening the file {0}".format(filepath)
	exit()

movieArray = []
repetedmov=[]
tugalinks= []
repetedlink=[]
print "Updating Movies database on:\t" + str(libs)
filmes = getFilmes(libs)
print "Movies database update found "+ str(len(filmes))+ " movies!"
fileerro = open("errorLog_tugaIO.log","w")
lines = filestream.readlines()
tot = str(len(lines))
print  tot + " to Download:"
i=0
for line in lines:
	i+=1
	line=line.strip()
	#arr = line.strip().split(" -> ")
	#line= arr[0]
	#link=None
	#try:
	#	link= arr[1]
	#except:
	#	pass
	if valid(line) and not(line in tugalinks) and not commented(line):
		print "Get info from movie " + str(i) + "/" + tot 
		#try:
		tmp = TugaIo(line)
		#tmp.movieurl= link
		rep = intersect(filmes,tmp.alias)
		if not rep:
			movieArray.append(tmp)
			tugalinks.append(line)
		else:
			repetedmov.append(tmp)
			repetedlink.append(line)
			fileerro.write(">>ERROR: " + line + "\n")
			fileerro.write("\tDETAILS: Movie "  +tmp.moviename + " already on library with name: "+ rep+ ".\n")
			fileerro.write("--------------------------------------------\n")

		#except Exception as e:
		#	fileerro.write(">>ERROR_ADD: " + str(line) + "\n")
		#	fileerro.write("\tDETAILS: " + str(e.message) +"\n")
		#	fileerro.write("--------------------------------------------\n")
			
	else:
		fileerro.write(">>ERROR_INVALID_LINE: " + str(line) + "\n")
		if (line in tugalinks)or (line in repetedlink):
			fileerro.write("\tMovie Repeated\n")
		fileerro.write("--------------------------------------------\n")

filestream.close()
tot = str(len(movieArray))
print tot + " valid movies to Download."
i=0
for movie in movieArray:
	i+=1
	print "Download movie " + str(i) + "/" + tot 
	#try:
	movie.download(finalpathloc,fileerro,finalpath)
	#except Exception as e:
	#	fileerro.write(">>ERROR_DOWNLOAD: " + movie.moviename + "\n")
	#	fileerro.write("\tTUGAURL:" + movie.tugaurl + "\n")
	#	fileerro.write("\tMOVIEURL:" + movie.movieurl + "\n")
	#	fileerro.write("\tSUBS:" + movie.movieSubs + "\n")
	#	fileerro.write("\tPOSTER:" + movie.movieposter + "\n")
	#	fileerro.write("\n\tDETAILS: " + e.message +"\n")
	#	fileerro.write("------------------------------------\n")
if plexUpdate:
	try:
		plexforceupdate(plexserver)
	except Exception as e:
		fileerro.write(e.message+"\n")
		fileerro.write("------------------------------------\n")

fileerro.close()


purge(os.getcwd().strip(),"wget-log")
#os.popen("rm wget-log*")


