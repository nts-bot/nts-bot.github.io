
# Basic Libraries
import os, json, time, requests, re, pickle, urllib
from urllib.error import HTTPError
# Html Parser
from bs4 import BeautifulSoup as bs
# Browser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# PPrint
from pprint import pprint
# SPOTIFY API TOOL
import spotipy
# # Multiple Requests
import queue
# IMAGE PROCESSING TOOLS
import cv2
import base64
from PIL import Image
# THE TRANSLATOR & COMPARISON TOOLS
from googletrans import Translator
translator = Translator()
from unidecode import unidecode
from difflib import SequenceMatcher
# TIMEOUT FUNCTION
import functools
from threading import Thread
# Environment Variables
from dotenv import load_dotenv
load_dotenv()

def timeout(timeout):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout))]
            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e
            t = Thread(target=newFunc)
            t.daemon = True
            try:
                t.start()
                t.join(timeout)
            except Exception as je:
                print ('error starting thread')
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret
        return wrapper
    return deco

def perform_web_requests(addresses, no_workers):
    class Worker(Thread):
        def __init__(self, request_queue):
            Thread.__init__(self)
            self.queue = request_queue
            self.results = []

        def run(self):
            while True:
                content = self.queue.get()
                if content == "":
                    break
                request = urllib.request.Request(content)
                repeat = True
                c = 0
                while repeat and c<=10:
                    try:
                        c+=1
                        response = urllib.request.urlopen(request)
                        repeat = False
                    except HTTPError:
                        print(f'.HTTPERROR.:{c}',end='\r')
                        time.sleep(5.0)
                self.results.append(response.read())
                self.queue.task_done()

    # Create queue and add addresses
    q = queue.Queue()
    for url in addresses:
        q.put(url)

    # Workers keep working till they receive an empty string
    for _ in range(no_workers):
        q.put("")

    # Create workers and add tot the queue
    workers = []
    for _ in range(no_workers):
        worker = Worker(q)
        worker.start()
        workers.append(worker)
    # Join workers to wait till they finished
    for worker in workers:
        worker.join()

    # Combine results from all workers
    r = []
    for worker in workers:
        r.extend(worker.results)
    return r

class nts:

    def __init__(self):
        dr = os.getenv("directory")
        os.chdir(f"{dr}")
        self.showlist = [i.split('.')[0] for i in os.listdir('./tracklist/')]

    # LOCAL DATABASE
    @timeout(5.0)
    def _j2d(self,path):
        try:
            with open(f"{path}.json", 'r', encoding='utf-8') as f:
                w = json.load(f)
                return(dict(w))
        except FileNotFoundError:
            self._d2j(path,dict())
            return(dict())
        except PermissionError as error:
            print(f'Permission Error : {error}')
            time.sleep(0.5)
            return(self._j2d(path))
        
    @timeout(5.0)
    def _d2j(self,path,allot):
        try:
            if isinstance(allot,dict):
                with open(f"{path}.json", 'w', encoding='utf-8') as f:
                    json.dump(allot, f, sort_keys=True, ensure_ascii=False, indent=4)
            else:
                raise ValueError(f'You are trying to dump {type(allot)} instead dict()')
        except:
            print(f'Error When Storing JSON')
            time.sleep(0.5)
            self._d2j(path,allot)

    def prerun(self,json1,json2,meta=''):
        js1 = self._j2d(json1)
        js2 = self._j2d(json2)
        if meta:
            js2 = js2[meta]
        ok = [False]
        do = []
        for i in js1: # episodes
            if i not in js2:
                ok += [True]
                do += [i]
            else:
                if not meta:
                    for j in js1[i]: # tracks
                        if j not in js2[i]:
                            ok += [True]
                        else:
                            if not js2[i][j]:
                                ok += [True]
                            else:
                                ok += [False]
        if do:
            print(do)
        return(any(ok),do)

    # RUN SCRIPT

    def runscript(self,shows):
        self.connect()
        for show in shows:
            print(show)
            # SCRAPE
            cont = True
            try:
                rq, do = self.prerun(f"./tracklist/{show}",f"./meta",show)
            except:
                self.scrape(show,False)
                self.ntstracklist(show)
                rq = ''
            if rq:
                self.ntstracklist(show,do)
            elif rq != '':
                cont = False          
            if cont:
                # SEARCH/RATE
                rq, do = self.prerun(f"./tracklist/{show}",f"./spotify_search_results/{show}")
                if rq:
                    self.searchloop(show,['tracklist','spotify_search_results'],'search',do)
                rq, do = self.prerun(f"./tracklist/{show}",f"./spotify/{show}") 
                if rq:
                    self.searchloop(show,['tracklist','spotify','spotify_search_results'],'rate',do)
                    reset = True
                else:
                    reset = False
                # BANDCAMP
                rq, do = self.prerun(f"./tracklist/{show}",f"./bandcamp/{show}") 
                if rq:
                    self.searchloop(show,['tracklist','bandcamp','spotify'],'bandcamp',do)
                # ADD
                self.spotifyplaylist(show,reset=reset)
            # HTML
            self.showhtml(show)
        self.home()

    # WEBSCRAPING

    def browse(self,url,amount=100):
        options = webdriver.ChromeOptions() 
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.headless = True
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)

        driver.get(url)
        time.sleep(1.0)

        elem = driver.find_element(By.TAG_NAME,"body")
        no_of_pagedowns = amount
        while no_of_pagedowns:
            print(no_of_pagedowns, end='\r')
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.5)
            no_of_pagedowns-=1
        time.sleep(0.5)
        soup = bs(driver.page_source, "html.parser")
        driver.quit()
        return(soup)

    def scrape(self,show,short=False,amount=100):
        url = f"https://www.nts.live/shows/{show}"
        if short:
            soup = bs(self.req(url).content, "html.parser")
        else:
            soup = self.browse(url,amount)
        grid = soup.select(".nts-grid-v2")
        episodelist = self._j2d(f'./tracklist/{show}')

        # EPISODES ID

        for i in grid[0]:
            a = i.select('a')
            if a:
                href = a[0]['href']
                episode = href.split('/episodes/')[1]
                if episode not in episodelist.keys():
                    print(f'. . . . . . .{episode[-10:]}.', end='\r')
                    episodelist[episode] = dict()
                else:
                    print(f'. . . . . . .{episode[-5:]}. skip', end='\r')
            else:
                print('href failed')

        # EPISODES META

        episodemeta = soup.select('.nts-grid-v2-item__content')
        meta = self._j2d(f'./meta')
        try:
            x = meta[show]
        except KeyError:
            meta[show] = dict()
        for i in episodemeta:
            sub = i.select('.nts-grid-v2-item__header')[0]
            ep = sub['href'].split('/')[-1]
            date = sub.select('span')[0].text
            eptitle = sub.select('.nts-grid-v2-item__header__title')[0].text
            meta[show][ep] = {'title':eptitle,'date':date}
        self._d2j(f'./meta',meta)

        # ARTIST IMAGES

        imlist = [i.split('.')[0] for i in os.listdir('./jpeg/')]
        if show not in imlist:
            back = soup.select('.background-image')
            if back:
                img = re.findall('\((.*?)\)',back[0].get('style'))[0]
                img_data = requests.get(img).content
                extension = img.split('.')[-1]
                with open(f'./jpeg/{show}.{extension}', 'wb') as handler:
                    handler.write(img_data)
            else:
                print('. . . . . . . . .Image not found.', end='\r')

        # ARTIST BIO

        bio = soup.select('.bio')
        titlelist = self._j2d('./extra/titles')
        desklist = self._j2d('./extra/descriptions')
        if bio:
            title = bio[0].select('.bio__title')[0].select('h1')[0].text
            desk = bio[0].select('.description')[0].text
            if not title:
                print('title-failed',end='\r')
                title = show
            if not desk:
                print('description-missing',end='\r')
                desk = ''
        else:
            print('. . . . . . . . . .Bio not found', end='\r')
            title = ''
            desk = ''
        titlelist[show] = title
        desklist[show] = desk
            
        self._d2j('./extra/titles',titlelist)
        self._d2j('./extra/descriptions',desklist)
        self._d2j(f'./tracklist/{show}',episodelist)
        
    @timeout(10.0)
    def req(self,url):
        try:
            res = requests.get(url)
            return(res)
        except ConnectionError:
            print('Connection Error')
            time.sleep(1.0)
            self.req(url)

    def ntstracklist(self,show,episodes=[]):
        episodelist = self._j2d(f'./tracklist/{show}')
        if episodes:
            metabool = True
        else:
            episodes = episodelist
            metabool = False
        for episode in episodes:
            if episodelist[episode] and not metabool:
                pass
            elif (isinstance(episodelist[episode],dict) and not episodelist[episode]) or metabool:
                print(episode[:10], end='\r')
                url = f"https://www.nts.live/shows/{show}/episodes/{episode}"
                soup = bs(self.req(url).content, "html.parser")
                
                # meta
                meta = self._j2d(f'./meta')
                try:
                    x = meta[show]
                except KeyError:
                    meta[show] = dict()
                bt = soup.select('.episode__btn')
                date = bt[0]['data-episode-date']
                eptitle = bt[0]['data-episode-name']
                meta[show][episode] = {'title':eptitle,'date':date}
                self._d2j(f'./meta',meta)

                tracks = soup.select('.track')
                for j in range(len(tracks)):
                    print(f'{episode[:10]}:{j:02}', end='\r')
                    try:
                        episodelist[episode][f"{j:02}"] = {
                            "artist" : f"{tracks[j].select('.track__artist')[0].get_text()}",
                            "title" : f"{tracks[j].select('.track__title')[0].get_text()}"
                        }
                    except IndexError:
                        print('Index Error')
                        try:
                            episodelist[episode][f"{j:02}"] = {
                            "artist" : f"{tracks[j].select('.track__artist')[0].get_text()}",
                            "title" : ""
                        }
                        except IndexError:
                            episodelist[episode][f"{j:02}"] = {
                            "artist" : f"",
                            "title" : f"{tracks[j].select('.track__title')[0].get_text()}"
                        }
            else:
                episodelist[episode] = ''
        self._d2j(f'./tracklist/{show}',episodelist)

    # SPOTIFY API

    @timeout(5.0)
    def subconnect(self,index,pick):
        ''' CONNECTION FUNCTION w/ TIMEOUT '''
        self.user = os.getenv("ssr")
        callback = 'http://localhost:8888/callback'
        cid = os.getenv(f"{index[pick]}id")#('ssd')#
        secret = os.getenv(f"{index[pick]}st")#('sst')#
        self.sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=cid,client_secret=secret,redirect_uri=f"{callback}",scope=['ugc-image-upload','playlist-modify-public'],username=self.user), requests_timeout=5, retries=5)
        print('Testing . . .')
        test = self.sp.user(self.user)
        print('. . . . . . . . Successful',end='\r')

    def connect(self):
        ''' CONNECTION HANDLER ; VIA https://developer.spotify.com/dashboard/applications '''
        index = ['a','b','c','d','e','f','g','h','i','j','k','l']
        self.wait('connect',True)
        try:
            with open('./extra/spotipywebapi.pickle', 'rb') as handle:
                pick = pickle.load(handle)
            print(index[pick])
            self.subconnect(index,pick)
            self.wait('connect',False)
        except Exception:
            self.conexcp()

    def conexcp(self):
        ''' CLEAR CACHE IF CONNECTION ERROR/TIMEOUT & TRY AGAIN '''
        time.sleep(3.0)
        index = ['a','b','c','d','e','f','g','h','i','j','k','l']
        try:
            print('. . . . . . . . Unsuccessful',end='\r')
            dr = os.listdir()
            if ".cache-31yeoenly5iu5pvoatmuvt7i7ksy" in dr:
                os.remove(".cache-31yeoenly5iu5pvoatmuvt7i7ksy")

            with open('./extra/spotipywebapi.pickle', 'rb') as handle:
                pick = pickle.load(handle)
            pick += 1
            if pick == (len(index)-1):
                pick = 0

            print(index[pick])

            with open('./extra/spotipywebapi.pickle', 'wb') as handle:
                pickle.dump(pick, handle, protocol=pickle.HIGHEST_PROTOCOL)

            self.subconnect(index,pick)
            self.wait('connect',False)

        except Exception:
            self.conexcp()

    @timeout(10.0)
    def wait(self,path,op=True):
        if not op:
            with open(f'./extra/{path}.pickle', 'wb') as handle:
                pickle.dump(0, handle, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            try:
                with open(f'./extra/{path}.pickle', 'rb') as handle:
                    pick = pickle.load(handle)
                if pick == 0:
                    with open(f'./extra/{path}.pickle', 'wb') as handle:
                        pickle.dump(1, handle, protocol=pickle.HIGHEST_PROTOCOL)
                else:
                    print(f'.waiting. : {path}',end='\r')
                    time.sleep(1.0)
                    self.wait(path,op)
            except Exception as error:
                print(f'.other error. : {error}',end='\r')
                time.sleep(5.0)
                self.wait(path,op)

    # SPOTIFY SEARCH

    def pid(self,show):
        ''' GET/CREATE SHOW PLAYLIST ID '''
        pid = self._j2d('pid')
        try:
            shelf = pid[show]
            return(shelf)
        except KeyError: # new show
            #
            tim = self._j2d('./extra/srch')
            tim[show] = 1
            self._d2j('./extra/srch',tim)
            #
            try:
                im = [i for i in os.listdir('./jpeg/') if i.split('.')[0] == show][0]
                basewidth = 600
                img = Image.open(f'./jpeg/{im}')
                wpercent = (basewidth/float(img.size[0]))
                hsize = int((float(img.size[1])*float(wpercent)))
                img = img.resize((basewidth,hsize), Image.ANTIALIAS)
                img.save(f'./jpeg/{im}')
                img = cv2.imread(f'./jpeg/{im}')
                jpg_img = cv2.imencode('.jpg', img)
                b64_string = base64.b64encode(jpg_img[1]).decode('utf-8')
            except Exception as error:
                print(f'image failure for show : {show} : Error : {error}')
            ref = self.sp.user_playlist_create(self.user,f'{show}-nts',public=True,description=f"(https://www.nts.live/shows/{show})")
            self.sp.playlist_upload_cover_image(ref, b64_string)
            #
            pid[show] = ref['id']
            self._d2j('pid',pid)
            return(ref['id'])

    def searchloop(self,show,jsonlist,kind='search',episodelist=[]):
        # jsonlist = [TRACKLIST, DO-ON, ADDITIONALS]

        for jsondir in jsonlist:
            locals()[jsondir] = self._j2d(f'./{jsondir}/{show}')

        total = list(eval(jsonlist[0]).keys())
        if not episodelist:
            episodelist = eval(jsonlist[0])
        for episode in episodelist:
            multiple = []
            print(f'{show[:7]}{episode[:7]}. . . . . . . . . .{total.index(episode)}:{len(total)}.',end='\r')
            try:
                x = eval(jsonlist[1])[episode]
            except KeyError:
                eval(jsonlist[1])[episode] = dict()
                first = True
            ok = eval(jsonlist[0])[episode].keys()
            nk = eval(jsonlist[1])[episode].keys()
            vl = [i for i in eval(jsonlist[1])[episode].values()]
            if list(set(ok)-set(nk)) or (not all(vl)):
                for trdx in eval(jsonlist[0])[episode]:
                    second = False
                    try:
                        if not eval(jsonlist[1])[episode][trdx]:
                            second = True
                    except KeyError:
                        second = True
                    if second:
                        first = True
                        print(f'{show[:7]}{episode[:7]}. . . . .{list(ok).index(trdx)}:{len(list(ok))}.',end='\r')
                        if kind == 'search':
                            # 0 : TRACKLIST ; 1 : SEARCH
                            eval(jsonlist[1])[episode][trdx] = self.spotifysearch(eval(jsonlist[0]),episode,trdx)
                        elif kind == 'rate':
                            # 0 : TRACKLIST ; 1 : RATE ; 2 : SEARCH
                            eval(jsonlist[1])[episode][trdx] = self.spotifyrate(eval(jsonlist[0]),eval(jsonlist[2]),episode,trdx)
                        elif kind == 'bandcamp':
                            # 0 : TRACKLIST ; 1 : BANDCAMP ; 2 : RATE
                            # eval(jsonlist[1])[episode][trdx] = self.bandcamp(eval(jsonlist[0]),eval(jsonlist[2]),episode,trdx)
                            multiple += [trdx]

            if first or multiple:
                if kind == 'bandcamp':
                    req = self.bandcamp_version2(eval(jsonlist[0]),eval(jsonlist[2]),episode,multiple)
                    for td in multiple:
                        eval(jsonlist[1])[episode][td] = req[td]
                if kind == 'rate':
                    ''' REMOVE UNKNOWNS '''
                    for j in eval(jsonlist[1]):
                        for k in eval(jsonlist[1])[j]:
                            if 'Unknown Artist' in eval(jsonlist[1])[j][k]['artist']:
                                eval(jsonlist[1])[j][k]["ratio"] = -1
                                eval(jsonlist[1])[j][k]["uri"] = ''
                            if 'Unknown' == eval(jsonlist[1])[j][k]['artist']:
                                eval(jsonlist[1])[j][k]["ratio"] = -1
                                eval(jsonlist[1])[j][k]["uri"] = ''
                self._d2j(f'./{jsonlist[1]}/{show}',eval(jsonlist[1]))

    def spotifysearch(self,showson,episode,trdx):
        q0= f'artist:{showson[episode][trdx]["artist"]} track:{showson[episode][trdx]["title"]}'
        q1 = f'{showson[episode][trdx]["artist"]} : {showson[episode][trdx]["title"]}'
        s0 = self._run(q0)
        s1 = self._run(q1)
        
        if s0['tracks']['items']:
            S0 = [{'artist':j['artists'][0]['name'],
                'title':j['name'],
                'uri':j['uri'].split(':')[-1]} 
                for j in s0['tracks']['items'][:3]]
        else:
            S0 = ''
        if s1['tracks']['items']:
            S1 = [{'artist':j['artists'][0]['name'],
                'title':j['name'],
                'uri':j['uri'].split(':')[-1]} 
                for j in s1['tracks']['items'][:3]]
        else:
            S1 = ''
        return({'s0':S0,'s1':S1})

    def spotifyrate(self,showson,srchson,episode,trdx):

        qa = showson[episode][trdx]["artist"]
        qt = showson[episode][trdx]["title"]
        s0 = srchson[episode][trdx]['s0']
        s1 = srchson[episode][trdx]['s1']

        if all([qa,qt]) and (qa,qt != 'Unknown') and ('Unknown Artist' not in qa):

            a0,t0,r0,u0 = self.test(s0,qa,qt)
            a1,t1,r1,u1 = self.test(s1,qa,qt)

            dx = [r0,r1].index(max([r0,r1]))

            if round(eval(f'r{dx}'),1) >= 0.4:
                lag = 1
            if round(eval(f'r{dx}'),1) >= 0.5:
                lag = 2
            if round(eval(f'r{dx}'),1) >= 0.6:
                lag = 3
            if round(eval(f'r{dx}'),1) >= 0.7:
                lag = 4
            if round(eval(f'r{dx}'),1) >= 0.8:
                lag = 5
            if round(eval(f'r{dx}'),1) >= 0.9:
                lag = 6
            if round(eval(f'r{dx}'),1) < 0.4:
                lag = 0

            if any([a0,a1]):
                return({'artist':eval(f'a{dx}'),'title':eval(f't{dx}'),'ratio':lag,'trackid':eval(f'u{dx}')})
            else:
                return({'artist':eval(f'a{dx}'),'title':eval(f't{dx}'),'ratio':-1,'trackid':''})
        else:
            return({'artist':'','title':'','ratio':-1,'trackid':''})

    # SPOTIFY SEARCH/RATE SUBFUNCTIONS

    @timeout(15.0)
    def subrun(self,query):
        ''' RUN SPOTIFY API WITH TIMEOUT '''
        try:
            result = self.sp.search(q=query, type="track,artist")
            if result is None:
                raise RuntimeWarning('Spotify API Broken')
            else:
                return(result)
        except spotipy.SpotifyException as error:
            print(f'Spotify API Error')
            return({'tracks':{'items':''}})

    def _run(self,query):
        ''' RUN SPOTIFY API WITH TIMEOUT '''
        try:
            return(self.subrun(query))
        except Exception:
            self.connect()
            return(self.subrun(query))

    def trnslate(self,tex):
        ''' TRANSLATE RESULT IF TEXT IS NOT IN LATIN SCRIPT '''
        tbool = False
        convert = unidecode(tex)
        bl = SequenceMatcher(None,convert,tex).ratio()
        if bl < 0.01:
            trans = True
        else:
            trans = False
        if trans:
            time.sleep(0.5)
            ln = translator.detect(tex).lang
            print(f'. . . . . . . . . . . .{ln}.',end='\r')
            try:
                if ln != 'en':
                    time.sleep(0.5)
                    convert = translator.translate(tex,dest='en',src=ln).text
                    tbool = True
            except ValueError as error:
                print(f'{ln} : {error}')
                pass
            except Exception as error:
                try:
                    print('.trying api again.')
                    time.sleep(5.0)
                    convert = translator.translate(tex,dest='en',src=ln).text
                except Exception as error:
                    raise RuntimeError(f'.api. error : {error}')
        return(convert,tbool)

    def ratio(self,a,b):
        ''' GET SIMILARITY RATIO BETWEEN TWO STRINGS '''
        return(SequenceMatcher(None, self.refine(a.lower()), self.refine(b.lower())).ratio())

    def kill(self,text):
        ''' ELIMINATE DUPLICATES & UNNECESSARY CHARACTERS WITHIN STRING '''
        cv = text.replace('・',' ').replace('+',' ').replace(']',' ').replace('[',' ').replace(')',' ').replace('(',' ').replace('\'',' ').replace('\"',' ').replace('-',' ').replace('!',' ').replace('/',' ').replace(';',' ').replace(':',' ').replace('.',' ').replace(',',' ').split(' ')
        return(" ".join(dict.fromkeys(cv)))

    def refine(self,text,kill=True):
        ''' ELIMINATE UNNECCESARY WORDS WITHIN STRING '''
        if kill:
            text = self.kill(text)
        for i in list(range(1990,2022)):
            text = text.replace(str(i),'')
        return text.replace('selections','').replace('with ','').replace('medley','').replace('vocal','').replace('previously unreleased','').replace('remastering','').replace('remastered','').replace('various artists','').replace('vinyl','').replace('from','').replace('theme','').replace('motion picture soundtrack','').replace('soundtrack','').replace('full length','').replace('original','').replace(' mix ',' mix mix mix ').replace('remix','remix remix remix').replace('edit','edit edit edit').replace('live','live live live').replace('cover','cover cover cover').replace('acoustic','acoustic acoustic').replace('demo','demo demo demo').replace('version','').replace('feat.','').replace('comp.','').replace('vocal','').replace('instrumental','').replace('&','and').replace('zero','0').replace('one','1').replace('two','2').replace('three','3').replace('unsure','4').replace('almost','5').replace('six','6').replace('seven','7').replace('eight','8').replace('nine','9').replace('excerpt','').replace('single','').replace('album','').replace('anonymous','').replace('unknown','').replace('traditional','')

    def comp(self,a,b,c,d): #OA, #OT, #SA, #ST
        ''' COMPARISON FUNCTION '''
        k1, t1 = self.trnslate(a) # O AUTHOR
        k2, t2 = self.trnslate(b) # O TITLE
        k3, t3 = self.trnslate(c) # S AUTHOR
        k4, t4 = self.trnslate(d) # S TITLE

        r = [self.ratio(k1,k3), self.ratio(k3,k1), self.ratio(k1,k4), self.ratio(k4,k1)] # AUTHOR
        X1 = max(r)
        r = [self.ratio(k2,k3), self.ratio(k3,k2), self.ratio(k2,k4), self.ratio(k4,k2)] # TITLE
        Y1 = max(r)
        # r = [self.ratio(f'{k1} {k2}',f'{k3} {k4}'), self.ratio(f'{k3} {k4}',f'{k1} {k2}'), self.ratio(f'{k2} {k1}',f'{k3} {k4}'), self.ratio(f'{k1} {k4}',f'{k2} {k1}')] # TOGETHER
        Z1 = (X1 + Y1)/2

        G = list(map(set,[k1.split(' '),k2.split(' '),k3.split(' '),k4.split(' ')]))
        k1 = ' '.join(list(G[0]-G[2]-G[3]))
        k2 = ' '.join(list(G[1]-G[2]-G[3]))
        k3 = ' '.join(list(G[2]-G[0]-G[1]))
        k4 = ' '.join(list(G[3]-G[0]-G[1]))

        # print([k1,k2,k3,k4])

        r = [self.ratio(k1,k3), self.ratio(k3,k1), self.ratio(k1,k4), self.ratio(k4,k1)] # AUTHOR
        try:
            x = min(i for i in r if i not in [0,1])
        except:
            x = 1
        r = [self.ratio(k2,k3), self.ratio(k3,k2), self.ratio(k2,k4), self.ratio(k4,k2)] # TITLE
        try:
            y = min(i for i in r if i not in [0,1])
        except:
            y = 1

        # print(x,y)
        # print(f'X1 : {X1} ; Y1 : {Y1} ; Z1 : {Z1}')

        if not (x == 1 and y == 1):
            X1 = (X1 + min(x,y))/2
            Y1 = (Y1 + min(x,y))/2
            Z1 = (Z1 + min(x,y))/2

        # print(f'X1 : {X1} ; Y1 : {Y1} ; Z1 : {Z1}')

        return((X1+Y1+Z1)/3)

    def test(self,search,queryartist,querytitle):
        ''' TESTING EACH SEARCH RESULT SYSTEMATICALLY, AND RETURNING THE BEST RESULT '''
        if search:
            arts = []
            tits = []
            rats = []
            uris = []
            for t in range(len(search)):
                arts += [search[t]['artist']]
                tits += [search[t]['title']]
                uris += [search[t]['uri']]
                comparison = self.comp(queryartist,querytitle,arts[t],tits[t])
                rats += [comparison]
            dx = rats.index(max(rats))
            return(arts[dx],tits[dx],rats[dx],uris[dx])
        else:
            return('','',0,'')

    # SPOTIFY PLAYLIST

    def scene(self,sequence):
        ''' GET UNIQUE ITEMS IN LIST & IN ORDER '''
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def spotifyplaylist(self,show,threshold=[3,10],remove=False,reset=False):
        ''' APPEND/CREATE/REMOVE FROM SPOTIFY PLAYLIST '''
        pid = self.pid(show)
        rate = self._j2d(f'./spotify/{show}')
        meta = self._j2d(f'./meta')[show]
        sortmeta = sorted(['.'.join(value['date'].split('.')[::-1]),key] for (key,value) in meta.items())

        tid = []
        pup = []
        mis = 0
        almost = 0
        unsure = 0

        for mt in sortmeta[::-1]:
            episodes = mt[1]
            for track in rate[episodes]:
                if threshold[0] <= rate[episodes][track]['ratio'] <= threshold[1]:
                    tid += [rate[episodes][track]['trackid']]
                pup += [rate[episodes][track]['trackid']]
                if not rate[episodes][track]['trackid']:
                    mis += 1
                if threshold[0]  <= rate[episodes][track]['ratio'] == 4:
                    almost += 1
                if threshold[0]  <= rate[episodes][track]['ratio'] <= 3:
                    unsure += 1

        tid = self.scene(tid[::-1])[::-1]

        current = self.sp.user_playlist_tracks(self.user,pid)
        tracks = current['items']
        while current['next']:
            current = self.sp.next(current)
            tracks.extend(current['items'])        
        ids = []
        for x in tracks:
            ids.append(x['track']['id'])

        if reset:
            rem = list(set(ids))
            hund = [rem[i:i+100] for i in range(0, len(rem), 100)]
            for i in hund:                    
                print(f'.resetting',end='\r')
                self.sp.user_playlist_remove_all_occurrences_of_tracks(self.user, pid, i)
            ids = []

        if remove:
            rem = list(set(ids) - set(tid))
            hund = [rem[i:i+100] for i in range(0, len(rem), 100)]
            for i in hund:                    
                print(f'.removing',end='\r')
                self.sp.user_playlist_remove_all_occurrences_of_tracks(self.user, pid, i)
        
        add = [i for i in tid if i not in ids]

        if add:
            hund = [add[i:i+100] for i in range(0, len(add), 100)]
            for i in hund:                    
                print(f'.tracks appended', end='\r')
                self.sp.user_playlist_add_tracks(self.user, pid, i) #, position=0
        else:
            print('.no tracks appended')

        if almost:
            almost = f'{almost} almost sure ;'
        else:
            almost = ''

        if unsure:
            unsure = f' {unsure} unsure ;'
        else:
            unsure = ''

        title, desk = self._j2d('./extra/titles')[show], self._j2d('./extra/descriptions')[show]
        desk = desk.replace('\n',' ').replace('\\','').replace('\"','').replace('\'','').strip()
        syn = f"[Archive of (www.nts.live/shows/{show}) : {almost}{unsure} {mis+len(set(pup))-len(set(tid))} missing. Tracks are grouped by episode]"
        
        x = self.sp.user_playlist_change_details(self.user,pid,name=f"{title} - NTS",description=f"{desk} {syn}")

    def follow(self,usr=1,kind='cre'):
        ''' SECONDARY SPOTIFY USERS WHO MAINTAIN ALPHABETICALLY ORGANIZED PLAYLISTS BELOW SPOTIFY (VISIBLE) PUBLIC PLAYLIST LIMIT (200) '''
        creds = self._j2d(f'{kind}dentials')
        user = creds[str(usr)]['user']
        cid = creds[str(usr)]['cid']
        secret = creds[str(usr)]['secret']
        callback = 'http://localhost:8888/callback'
        spot = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=cid,client_secret=secret,redirect_uri=f"{callback}",scope='playlist-modify-public user-follow-modify',username=user), requests_timeout=5, retries=5)
        print('Testing . . .')
        test = spot.user(user)
        print('. . . . . . . . Successful',end='\r')
        
        if kind == 'cre':
            extent = self.showlist[(200 * (usr - 1)):(200 * (usr))]
        elif kind == 'pre':
            extent = self.showlist

        print('Unfollowing')
        plys = []
        for i in range(4):
            it = spot.user_playlists(user,offset=(i * 50))['items']
            plys += [k['id'] for k in it]
        for i in plys:
            playlist_owner_id = '31yeoenly5iu5pvoatmuvt7i7ksy'
            spot.user_playlist_unfollow(playlist_owner_id, i)

        ## follow
        print('Following')
        print(f'{extent[0][0]} : {extent[-1][0]}')
        for i in extent[::-1]:
            print(i[:20],end='\r')
            playlist_owner_id = '31yeoenly5iu5pvoatmuvt7i7ksy'
            playlist_id = self.pid(i)
            if playlist_id:
                spot.user_playlist_follow_playlist(playlist_owner_id, playlist_id)
            else:
                print(f'FAILED : {i}')
        ## follow users
        del creds[str(usr)]
        u = []
        for i in creds:
            u += [creds[i]['user']]
        spot.user_follow_users(u)

    # BANDCAMP SEARCH

    def camp(self,query):
        tj = dict()
        url = f"https://bandcamp.com/search?q={query}&item_type=t"
        soup = bs(self.req(url).content, "html.parser")
        try:
            if soup.select('.noresults-header'):
                tj = -1
        except:
            try:
                tj['artist'] = soup.select('.subhead')[0].text.replace('\n','').split('by')[1].strip()
                tj['title'] = soup.select('.heading')[0].text.replace('\n','').strip()
                tj['url'] = soup.select('.itemurl')[0].text.replace('\n','').strip()
            except:
                # raise RuntimeError('REQUEST FAILED')
                print('REQUEST FAILED')
                time.sleep(5.0)
                return(self.camp(query))
        return(tj)

    def bandcamp(self,showson,rateson,episode,trdx):

        ort = showson[episode][trdx]["artist"] # original artist
        oit = showson[episode][trdx]["title"] # original title

        track = f'{ort} {oit}'
        quer1 = urllib.parse.quote(track)

        tl = self.camp(quer1)
        if not tl:
            if rateson[episode][trdx]['ratio'] >= 3:
                ort = rateson[episode][trdx]["artist"] # original artist
                oit = rateson[episode][trdx]["title"] # original title
                track = f'{ort} {oit}'
                quer2 = urllib.parse.quote(track)
                tl = self.camp(quer2)
            else:
                quer2 = urllib.parse.quote(self.refine(unidecode(track),False))
                tl = self.camp(quer2)

        return(tl)

    def camp_version2(self,query):

        print(f'.{len(query)}.',end='\r')

        time.sleep(5.0)#(round(len(query)/3)+1.0)
        response = perform_web_requests(list(query.values()), 16)
        if not isinstance(response,list):
            response = [response]

        for i in range(len(query)):
            try:
                response[i]
            except IndexError:
                print('REQUEST FAILED')
                time.sleep(5.0)
                return(self.camp_version2(query))

        c=-1
        for td in query:
            c+=1
            soup = bs(response[c], "html.parser")
            # pot += [bs(resp, "html.parser")]
            try:
                if soup.select('.noresults-header'):
                    query[td] = -1
            except:
                query[td]['artist'] = soup.select('.subhead')[0].text.replace('\n','').split('by')[1].strip()
                query[td]['title'] = soup.select('.heading')[0].text.replace('\n','').strip()
                query[td]['url'] = soup.select('.itemurl')[0].text.replace('\n','').strip()
                break
        # return(pot)
        return(query)

    def bandcamp_version2(self,showson,rateson,episode,multiple):
        
        q1 = dict()
        q2 = dict()
        q3 = dict()
        for td in multiple:
            track = f'{showson[episode][td]["artist"]} {showson[episode][td]["title"] }'
            q1[td] = f"https://bandcamp.com/search?q={urllib.parse.quote(track)}&item_type=t"
            if rateson[episode][td]['ratio'] >= 3:
                spot = f'{rateson[episode][td]["artist"]} {rateson[episode][td]["title"] }'
                q2[td] = f"https://bandcamp.com/search?q={urllib.parse.quote(spot)}&item_type=t"
            else:
                q2[td] = f"https://bandcamp.com/search?q={urllib.parse.quote(self.refine(unidecode(track),False))}&item_type=t"

        reply = self.camp_version2(q1)
        qsuccess = {i : reply[i] for i in reply if reply[i] != -1}
        qfailure = {i : reply[i] for i in reply if reply[i] == -1}
        if qfailure:
            q2 = {i:q2[i] for i in q2 if i not in qsuccess}
            reply = self.camp_version2(q2)
            qsuccess |= {i : reply[i] for i in reply if reply[i] != -1}
            qfailure = {i : reply[i] for i in reply if reply[i] == -1}

        return(qfailure | qsuccess)

        

    # HTML

    def home(self): # HTML HOME
        doc = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>
        <meta content="HTML Tidy for HTML5 for Linux version 5.6.0" name="generator"/>
        <meta content="IE=edge" http-equiv="X-UA-Compatible"/>
        <title>
        NTS-bot
        </title>
        <meta content="width=device-width,initial-scale=1" name="viewport"/>
        <link href="./assets/stylesheet.css" rel="stylesheet"/>
        <link rel="icon" href="./assets/Nts-radio.jpg">
        </head>
        <body>
            <h1><a href="https://github.com/nts-bot/nts-bot.github.io">GitHub</a></h1>
        """

        # [1] index
        
        doc += '<div><h2>index</h2></div>'
        title = self._j2d('./extra/titles')

        for shw in self.showlist:
            ''' CREATE LIST OF SHOW TITLES ALPHABETICALLY (LIST) '''
            tit = title[shw]
            V = shw[0].lower()

            if V not in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']:
                if 'Ø' not in locals():
                    locals()['Ø'] = [tit]
                else: 
                    locals()['Ø'] += [tit]
            else:
                if V not in locals():
                    locals()[V] = [tit]
                else:
                    locals()[V] += [tit]

        for shw in ['Ø','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']:
            try:
                term = eval(shw)
                doc += f"""<details><summary><h3><div class="title">{shw.upper()} ↫</div></h3></summary><ol>"""
                for how in term:
                    try:
                        name = list(title.keys())[list(title.values()).index(how)]
                    except ValueError:
                        name = list(title.keys())[list(title.keys()).index(how)]
                    doc += f"""<li><a class="show" href="./html/{name}.html">{how}</li>"""
                doc += f"""</details>"""
            except NameError as error:
                print(f'{shw} : {error}')            

        doc += '''<br><br><br><br></body></html>'''

        ''' [03] SOUPIFY AND SAVE '''

        soup = bs(doc, "lxml")
        pretty = soup.prettify() 
        with open(f"index.html", 'w', encoding='utf8') as f:
            f.write(pretty)

    def showhtml(self,show):
        doc = """
            <!DOCTYPE html>
            <html>
            <head>
            <meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>
            <meta content="HTML Tidy for HTML5 for Linux version 5.6.0" name="generator"/>
            <meta content="IE=edge" http-equiv="X-UA-Compatible"/>
            <title>
            NTS-bot
            </title>
            <meta content="width=device-width,initial-scale=1" name="viewport"/>
            <link href="../assets/stylesheet.css" rel="stylesheet"/>
            <link rel="icon" href="../assets/Nts-radio.jpg">
            </head>
            <body>
                <h1><a href="https://github.com/nts-bot/nts-bot.github.io">GitHub</a></h1>
            """
        pid = self._j2d('pid')[show]
        title = self._j2d('./extra/titles')
        doc += f'<div><h2><a href="https://nts.live/shows/{show}">{title[show]}</a></h2><br><blockquote>⚫⚪ = Listen Back [NTS]<br>🟢 = Spotify<br><img src="../assets/bandcamp-logo-alt.png" class="icon"/> = Bandcamp<br><a href="https://open.spotify.com/playlist/{pid}">⭕ - Show Playlist</a></blockquote></div>' # Show Title Spotify_icon.svg

        # For each episode : collapsable details / tracklist / ntslink / spotifylink / bandcamplink

        episodes = self._j2d(f'./tracklist/{show}')
        spotify = self._j2d(f'./spotify/{show}')
        bandcamp = self._j2d(f'./bandcamp/{show}')
        meta = self._j2d(f'./meta')[show]
        sortmeta = sorted(['.'.join(value['date'].split('.')[::-1]),key] for (key,value) in meta.items())

        for mt in sortmeta[::-1]:

            i = mt[1]
            ti = f"{meta[i]['title']} - {meta[i]['date']}"

            doc += f'<details><summary><h3><div class="title">{ti}</div><span class="data"><a href="https://nts.live/shows/{show}/episodes/{i}">⚫⚪</a></span></h3></summary>'
            doc += '<ol>'

            for j in episodes[i]:

                tart = episodes[i][j]['artist']
                ttit = episodes[i][j]['title']

                try:
                    bc = bandcamp[i][j]['url']
                    bnd = f"""<a class="goto" href="{bc}"><img src="../assets/bandcamp-logo-alt.png" class="icon"/></a>  """
                except:
                    bnd = ''
                
                try:
                    if spotify[i][j]['ratio'] >= 3:
                        sp = f"""https://open.spotify.com/track/{spotify[i][j]['trackid']}"""
                        spo = f"""<a class="goto" href="{sp}">🟢</a>  """
                    else:
                        spo = ''
                except:
                    spo = ''

                if any([bnd,spo]):
                    colon = ':'
                else:
                    colon = ''

                doc += f"""<li>{tart} - {ttit}   {colon}   <span class="data">{spo}{bnd}</span></li>""" #{tub}

            doc += '</ol></details>'

        doc += '''<br><br><br></body></html>'''

        ''' [03] SOUPIFY AND SAVE '''

        soup = bs(doc, "lxml")
        pretty = soup.prettify() 
        with open(f"./html/{show}.html", 'w', encoding='utf8') as f:
            f.write(pretty)

#