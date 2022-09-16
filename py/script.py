# BASIC LIBRARIES
from importlib.resources import contents
import os, json, time, requests, re, pickle, urllib
from urllib.error import HTTPError
# HTML PARSER
from bs4 import BeautifulSoup as bs
# BROWSER
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
# MULTITHREADING TASKS
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
from threading import Thread, Lock
# ENVIRONMENT VARIABLES
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

class nts:

    def __init__(self):
        dr = os.getenv("directory")
        os.chdir(f"{dr}")
        self.showlist = [i.split('.')[0] for i in os.listdir('./tracklist/')]

    # LOCAL DATABASE
    # @timeout(5.0)
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
        
    # @timeout(5.0)
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
                            do += [i]
                        else:
                            if not js2[i][j]:
                                ok += [True]
                                do += [i]
                            else:
                                ok += [False]
        do = self.scene(do)
        if do:
            print(f'.{json1[2:5]}:{json2[2:5]}:{len(do)}.',end='\r')
        return(any(ok),do)

    # RUN SCRIPT

    def runscript(self,shows):
        self.connect()
        o = {i:shows[i] for i in range(len(shows))}
        print(o)
        for i in range(len(shows)):
            show = shows[i]
            oo = show + '. . . . . . . . . . . . . . . . . . . . . . . .'
            print(f'{oo[:50]}{i}/{len(shows)}')
            time.sleep(0.1)
            # SCRAPE
            if show in self._j2d(f'./meta'): # WIP
                self.scrape(show,True)
                rq, do = self.prerun(f"./tracklist/{show}",f"./meta",show) #meta
                self.ntstracklist(show,do)
            else:
                self.scrape(show,False,amount=10) # CHANGE AMOUNT TO 100 TO GET FULL EPISODELIST
                rq, do = self.prerun(f"./tracklist/{show}",f"./meta",show) #meta
                self.ntstracklist(show,do)
            # SEARCH/RATE
            rq, do = self.prerun(f"./tracklist/{show}",f"./spotify_search_results/{show}")
            if rq:
                self.searchloop(show,['tracklist','spotify_search_results'],'search',do)
            #
            rq, do = self.prerun(f"./tracklist/{show}",f"./spotify/{show}") 
            if rq:
                self.searchloop(show,['tracklist','spotify','spotify_search_results'],'rate',do)
            # BANDCAMP # TODO
            # rq, do = self.prerun(f"./tracklist/{show}",f"./bandcamp/{show}") 
            # if rq:
            #     self.searchloop(show,['tracklist','bandcamp','spotify'],'bandcamp',do)
            # ADD
            if show not in self._j2d('./uploaded'):
                self.spotifyplaylist(show)
            else:
                rq, do = self.prerun(f"./tracklist/{show}",f"./uploaded",show) 
                if rq: # or (show not in self._j2d('./extra/dflag'))
                    self.spotifyplaylist(show)
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
        meta = self._j2d(f'./meta')
        if not episodes:
            episodes = episodelist
        for episode in episodes:
            if episodelist[episode]:
                pass
            elif isinstance(episodelist[episode],dict): # and not episodelist[episode]
                print(episode[:10], end='\r')
                url = f"https://www.nts.live/shows/{show}/episodes/{episode}"
                soup = bs(self.req(url).content, "html.parser")
                
                # meta
                if show not in meta:
                    meta[show] = dict()
                try:
                    bt = soup.select('.episode__btn')
                    date = bt[0]['data-episode-date']
                    eptitle = bt[0]['data-episode-name']
                    meta[show][episode] = {'title':eptitle,'date':date}
                except:
                    try:
                        print(f'.trying-once-more-to-find-meta.')
                        soup = self.browse(url,1)
                        bt = soup.select('.episode__btn')
                        date = bt[0]['data-episode-date']
                        eptitle = bt[0]['data-episode-name']
                        meta[show][episode] = {'title':eptitle,'date':date}
                    except:
                        print(f'FAILURE PROCESSING META : {show}:{episode}\n')
                    

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
        self._d2j(f'./meta',meta)
        self._d2j(f'./tracklist/{show}',episodelist)

    # SPOTIFY API

    @timeout(15.0)
    def subconnect(self,index,pick):
        ''' CONNECTION FUNCTION w/ TIMEOUT '''
        self.user = os.getenv("ssr")
        callback = 'http://localhost:8888/callback'
        cid = os.getenv(f"{index[pick]}id")#('ssd')#
        secret = os.getenv(f"{index[pick]}st")#('sst')#
        self.sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=cid,client_secret=secret,redirect_uri=f"{callback}",scope=['ugc-image-upload','playlist-modify-public'],username=self.user), requests_timeout=5, retries=5)
        print('. Testing . ',end='')
        test = self.sp.user(self.user)
        print('Successful',end='\r')

    def connect(self):
        ''' CONNECTION HANDLER ; VIA https://developer.spotify.com/dashboard/applications '''
        index = ['a','b','c','d','e','f','g','h','i','j','k','l']
        self.wait('connect',True)
        try:
            with open('./extra/spotipywebapi.pickle', 'rb') as handle:
                pick = pickle.load(handle)
            print(index[pick],end=' ')
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

    # @timeout(10.0)
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
                    # print(f'.{path}.',end='\r')
                    time.sleep(0.1)
                    self.wait(path,op)
            except Exception as error:
                print(f'.W.{error}.',end='\r')
                time.sleep(1.0)
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
            pid[show] = ref['id']
            self._d2j('pid',pid)
            self.sp.playlist_upload_cover_image(ref['id'], b64_string)
            #
            return(ref['id'])

    def searchloop(self,show,jsonlist,kind='search',episodelist=[]):
        
        '''jsonlist = [TRACKLIST, DO-ON, ADDITIONALS] ''' 
        for jsondir in jsonlist:
            locals()[jsondir] = self._j2d(f'./{jsondir}/{show}')

        total = list(eval(jsonlist[0]).keys())
        if not episodelist:
            episodelist = eval(jsonlist[0])

        multiple = dict()

        for episode in episodelist:
            multiple[episode] = dict()
            print(f'{show[:7]}{episode[:7]}. . . . . . . . . .{total.index(episode)}:{len(total)}.',end='\r')
            if episode not in eval(jsonlist[1]):
                eval(jsonlist[1])[episode] = dict()
                self._d2j(f'./{jsonlist[1]}/{show}',eval(jsonlist[1]))
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
                        print(f'{show[:7]}{episode[:7]}. . . . .{list(ok).index(trdx)}:{len(list(ok))}.',end='\r')
                        if kind == 'search':
                            # 0 : TRACKLIST ; 1 : SEARCH
                            # eval(jsonlist[1])[episode][trdx] = self.spotifysearch(eval(jsonlist[0]),episode,trdx)
                            multiple[episode][trdx] = 0
                        elif kind == 'rate':
                            # 0 : TRACKLIST ; 1 : RATE ; 2 : SEARCH
                            # eval(jsonlist[1])[episode][trdx] = self.spotifyrate(eval(jsonlist[0]),eval(jsonlist[2]),episode,trdx)
                            multiple[episode][trdx] = 0
                        elif kind == 'bandcamp':
                            # 0 : TRACKLIST ; 1 : BANDCAMP ; 2 : RATE
                            # eval(jsonlist[1])[episode][trdx] = self.bandcamp(eval(jsonlist[0]),eval(jsonlist[2]),episode,trdx)
                            multiple[episode][trdx] = 0
    
        if any([True for i in multiple if multiple[i]]):
            if kind == 'search':
                req = self.mt_spotifysearch(eval(jsonlist[0]),multiple)
            elif kind == 'rate':
                # if len(multiple) <= 3:
                req = self.mt_spotifyrate(eval(jsonlist[0]),eval(jsonlist[2]),multiple)
                # else:
                #     req = dict()
                #     keys = list(multiple.keys())
                #     n = 2
                #     for di in range(0,len(keys),n):
                #         subdic = {k: multiple[k] for k in keys[di: di + n]}
                #         req |= self.mt_spotifyrate(eval(jsonlist[0]),eval(jsonlist[2]),subdic)
            elif kind == 'bandcamp':
                req = self.mt_bandcamp(eval(jsonlist[0]),eval(jsonlist[2]),multiple)
            for episode in multiple:
                for td in multiple[episode]:
                    eval(jsonlist[1])[episode][td] = req[episode][td]
            self._d2j(f'./{jsonlist[1]}/{show}',eval(jsonlist[1]))

    def spotifysearch(self,showson,episode,trdx):
        ''' Not Used '''
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

    @timeout(50.0)
    def subrun(self,query):
        ''' RUN SPOTIFY API WITH TIMEOUT '''
        try:
            result = self.sp.search(q=query, type="track,artist")
            if result is None:
                raise RuntimeWarning('Spotify API Broken')
            else:
                return(result)
        except spotipy.SpotifyException as error:
            print(f'.spotify-api-error.',end='\r')
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
        convert = unidecode(tex)
        bl = SequenceMatcher(None,convert,tex).ratio()
        if bl < 0.01:
            trans = True
        else:
            trans = False
        if trans:
            time.sleep(0.5)
            ln = translator.detect(tex).lang
            # print(f'({ln})',end='\r')
            if ln != 'en':
                tr = True
                c = 0
                while tr:
                    c += 1
                    # print(f'<t{c}>',end='\r')
                    try:
                        time.sleep(0.5)
                        convert = translator.translate(tex,dest='en',src=ln).text
                        # print(f' {" "*len(ln)} ',end='\r')
                        tr=False
                    except ValueError as error:
                        print(f'{ln} : {error}',end='\r')
                        tr=False
                        pass
                    except Exception:
                        # print(f'[{c}/TTA]',end='\r')
                        print(f'[{c}]',end='\r')
                        time.sleep(1.0)
                        pass
        return(convert)

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
        k1 = self.trnslate(a) # O AUTHOR
        k2 = self.trnslate(b) # O TITLE
        k3 = self.trnslate(c) # S AUTHOR
        k4 = self.trnslate(d) # S TITLE

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

    def spotifyplaylist(self,show,threshold=[3,10],reset=False): #remove=False,
        ''' APPEND/CREATE/REMOVE FROM SPOTIFY PLAYLIST '''
        pid = self.pid(show)
        rate = self._j2d(f'./spotify/{show}')
        meta = self._j2d(f'./meta')[show]
        #
        uploaded = self._j2d(f'./uploaded')
        if show not in uploaded:
            uploaded[show] = dict()
            reset = True
        #   
        sortmeta = sorted(['.'.join(value['date'].split('.')[::-1]),key] for (key,value) in meta.items())
        #
        tid = []
        trackdict = dict()
        pup = []
        mis = 0
        almost = 0
        unsure = 0

        fp = sortmeta[0][0].split('.')
        firstep = f"{fp[2]}.{fp[1]}.{fp[0]}"
        lp = sortmeta[-1][0].split('.')
        lastep = f"{lp[2]}.{lp[1]}.{lp[0]}"

        for mt in sortmeta[::-1]:
            episodes = mt[1]
            trackdict[episodes] = []
            if episodes not in uploaded[show]:
                uploaded[show][episodes] = 1
                for track in rate[episodes]:
                    if threshold[0] <= rate[episodes][track]['ratio'] <= threshold[1]:
                        tid += [rate[episodes][track]['trackid']]
                        trackdict[episodes] += [rate[episodes][track]['trackid']]
                    pup += [rate[episodes][track]['trackid']]
                    if not rate[episodes][track]['trackid']:
                        mis += 1
                    if threshold[0]  <= rate[episodes][track]['ratio'] == 4:
                        almost += 1
                    if threshold[0]  <= rate[episodes][track]['ratio'] <= 3:
                        unsure += 1
            else:
                pass
        if tid:
            
            tidup = self.scene(tid[::-1])[::-1]
            dups = len(tid) - len(tidup)
            
            current = self.sp.user_playlist_tracks(self.user,pid)
            tracks = current['items']
            #
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

            print(f'.tracks appending.', end='\r')
            for episode in list(trackdict.keys())[::-1]:
                if trackdict[episode]:
                    trackstoadd = trackdict[episode]
                    hund = [trackstoadd[i:i+100] for i in range(0, len(trackstoadd), 100)]
                    for i in hund:
                        self.sp.user_playlist_add_tracks(self.user, pid, i,0)
            print(f'.tracks appended.', end='\r')


            if almost:
                almost = f'{almost} almost sure ;'
            else:
                almost = ''

            if unsure:
                unsure = f' {unsure} unsure ;'
            else:
                unsure = ''

            duplicates = f' {dups} repeated ;'

            title, desk = self._j2d('./extra/titles')[show], self._j2d('./extra/descriptions')[show]
            desk = desk.replace('\n',' ').replace('\\','').replace('\"','').replace('\'','').strip()
            syn = f"[Archive of (www.nts.live/shows/{show}) : {almost}{unsure}{duplicates} {mis+len(set(pup))-len(set(tid))} missing. ordered {lastep}-to-{firstep}]"
            
            x = self.sp.user_playlist_change_details(self.user,pid,name=f"{title} - NTS",description=f"{desk} {syn}")
            self._d2j(f'./uploaded',uploaded)
        else:
            print('.no tracks to append.')

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

    def upndict(self,new,old):
        for episode in new:
            for td in new[episode]:
                if td not in old[episode]:
                    old[episode][td] = new[episode][td]
                else:
                    raise RuntimeError('DICTIONARY UPDATE SCRIPT FAILED')
        return(old)
        
    # MULTITHREADING FUNCTIONS

    def mt_request(self,content):
        c = 0
        request = urllib.request.Request(content)
        repeat = True
        while repeat:
            try:
                c+=1
                return(urllib.request.urlopen(request).read())
                repeat = False
            except HTTPError:
                print(f'. . . . .RE:{c}.',end='\r')
                time.sleep(1.0)

    def mt_spotifysearch(self,showson,multiple):

        q1 = dict()
        q2 = dict()
        for episode in multiple:
            q1[episode] = dict()
            q2[episode] = dict()
            for td in multiple[episode]:
                q1[episode][td] = f'artist:{showson[episode][td]["artist"]} track:{showson[episode][td]["title"]}'
                q2[episode][td] = f'{showson[episode][td]["artist"]} : {showson[episode][td]["title"]}'

        return(self.mt_samp(q1,q2))

    def mt_samp(self,q1,q2):

        # flatten queries
        Q1, Q2 = [q1[l1][l2] for l1 in q1 for l2 in q1[l1]], [q2[l1][l2] for l1 in q2 for l2 in q2[l1]]
        print(f'.{len(Q1)}.{len(Q2)}')

        taskdict = {f"q1.{l1:03}.{l2:03}":q1[list(q1.keys())[l1]][list(q1[list(q1.keys())[l1]].keys())[l2]] 
                    for l1 in range(len(q1)) 
                    for l2 in range(len(q1[list(q1.keys())[l1]]))
                    }
        taskdict |= {f"q2.{l1:03}.{l2:03}":q2[list(q2.keys())[l1]][list(q2[list(q2.keys())[l1]].keys())[l2]] 
                    for l1 in range(len(q2)) 
                    for l2 in range(len(q2[list(q2.keys())[l1]]))
                    }

        # run syncronious mass request
        time.sleep(1.0)
        taskdict = multithreading(taskdict, 16, 'spotify') #_run
        #
        for l1 in range(len(q1)):
            episode = list(q1.keys())[l1]
            for l2 in range(len(q1[list(q1.keys())[l1]])): # td are tracks
                td = list(q1[list(q1.keys())[l1]].keys())[l2]
                if taskdict[f"q1.{l1:03}.{l2:03}"]['tracks']['items']:
                    S0 = [{'artist':j['artists'][0]['name'],
                        'title':j['name'],
                        'uri':j['uri'].split(':')[-1]} 
                        for j in taskdict[f"q1.{l1:03}.{l2:03}"]['tracks']['items'][:3]]
                else:
                    S0 = ''
                if taskdict[f"q1.{l1:03}.{l2:03}"]['tracks']['items']:
                    S1 = [{'artist':j['artists'][0]['name'],
                        'title':j['name'],
                        'uri':j['uri'].split(':')[-1]} 
                        for j in taskdict[f"q1.{l1:03}.{l2:03}"]['tracks']['items'][:3]]
                else:
                    S1 = ''

                q1[episode][td] = {'s0':S0,'s1':S1}

        return(q1)

    def mt_spotifyrate(self,showson,srchson,multiple):

        q1 = dict()
        q2 = dict()
        for episode in multiple:
            q1[episode] = dict()
            q2[episode] = dict()
            for td in multiple[episode]:
                
                qa = showson[episode][td]["artist"]
                qt = showson[episode][td]["title"]
                s0 = srchson[episode][td]['s0']
                s1 = srchson[episode][td]['s1']

                if all([qa,qt]) and (qa,qt != 'Unknown') and ('Unknown Artist' not in qa):
                    q1[episode][td] = {'s':s0,'qa':qa,'qt':qt}
                    q2[episode][td] = {'s':s1,'qa':qa,'qt':qt}
                else:
                    q1[episode][td] = {'s':'','qa':'','qt':''}
                    q2[episode][td] = {'s':'','qa':'','qt':''}

        return(self.mt_rate(q1,q2))

    def mt_rate(self,q1,q2):

        # flatten queries
        Q1, Q2 = [q1[l1][l2] for l1 in q1 for l2 in q1[l1]], [q2[l1][l2] for l1 in q2 for l2 in q2[l1]]
        print(f'.{len(Q1)}.{len(Q2)}')

        taskdict = {f"q1.{l1:03}.{l2:03}":q1[list(q1.keys())[l1]][list(q1[list(q1.keys())[l1]].keys())[l2]] 
                    for l1 in range(len(q1)) 
                    for l2 in range(len(q1[list(q1.keys())[l1]]))
                    }
        taskdict |= {f"q2.{l1:03}.{l2:03}":q2[list(q2.keys())[l1]][list(q2[list(q2.keys())[l1]].keys())[l2]] 
                    for l1 in range(len(q2)) 
                    for l2 in range(len(q2[list(q2.keys())[l1]]))
                    }

        taskdict = multithreading(taskdict, 8, 'rate') #_run
        
        for l1 in range(len(q1)):
            episode = list(q1.keys())[l1]
            for l2 in range(len(q1[list(q1.keys())[l1]])): # td are tracks
                td = list(q1[list(q1.keys())[l1]].keys())[l2]
                #
                a0,t0,r0,u0 = taskdict[f"q1.{l1:03}.{l2:03}"]['a'],taskdict[f"q1.{l1:03}.{l2:03}"]['t'],taskdict[f"q1.{l1:03}.{l2:03}"]['r'],taskdict[f"q1.{l1:03}.{l2:03}"]['u']
                a1,t1,r1,u1 = taskdict[f"q2.{l1:03}.{l2:03}"]['a'],taskdict[f"q2.{l1:03}.{l2:03}"]['t'],taskdict[f"q2.{l1:03}.{l2:03}"]['r'],taskdict[f"q2.{l1:03}.{l2:03}"]['u']
                #
                if ([a0,t0,r0,u0] != ['','',0,'']) or ([a1,t1,r1,u1] != ['','',0,'']):
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
                        q1[episode][td] = {'artist':eval(f'a{dx}'),'title':eval(f't{dx}'),'ratio':lag,'trackid':eval(f'u{dx}')}
                    else:
                        q1[episode][td] = {'artist':eval(f'a{dx}'),'title':eval(f't{dx}'),'ratio':-1,'trackid':''}
                else:
                    q1[episode][td] = {'artist':'','title':'','ratio':-1,'trackid':''}

        return(q1)

    def mt_bandcamp(self,showson,rateson,multiple):
        
        q1 = dict()
        q2 = dict()
        for episode in multiple:
            q1[episode] = dict()
            q2[episode] = dict()
            for td in multiple[episode]:
                track = f'{showson[episode][td]["artist"]} {showson[episode][td]["title"] }'
                q1[episode][td] = f"https://bandcamp.com/search?q={urllib.parse.quote(track)}&item_type=t"
                if rateson[episode][td]['ratio'] >= 3:
                    spot = f'{rateson[episode][td]["artist"]} {rateson[episode][td]["title"] }'
                    q2[episode][td] = f"https://bandcamp.com/search?q={urllib.parse.quote(spot)}&item_type=t"
                else:
                    q2[episode][td] = f"https://bandcamp.com/search?q={urllib.parse.quote(self.refine(unidecode(track),False))}&item_type=t"

        reply = self.mt_camp(q1)
        # qsuccess = {i : reply[i] for i in reply if reply[i] != -1}
        # {i:{j:a[i][j] for j in a[i] if a[i][j]!=-1} for i in a}
        qsuccess = {i:{j:reply[i][j] for j in reply[i] if reply[i][j]!=-1} for i in reply}
        qfailure = {i:{j:reply[i][j] for j in reply[i] if reply[i][j]==-1} for i in reply}
        if any([True for i in qfailure if qfailure[i]]):
            # q2 = {i:q2[i] for i in q2 if i not in qsuccess}
            q2 = {i:{j:q2[i][j] for j in q2[i] if j not in qsuccess[i]} for i in q2}
            if any([True for i in q2 if q2[i]]):
                reply = self.mt_camp(q2)
                qsuccess = self.upndict({i:{j:reply[i][j] for j in reply[i] if reply[i][j]!=-1} for i in reply},qsuccess)
                qfailure = {i:{j:reply[i][j] for j in reply[i] if reply[i][j]==-1} for i in reply}

        return(self.upndict(qfailure,qsuccess))

    def mt_camp(self,query): # WIP

        # flatten query
        querylist = [query[l1][l2] for l1 in query for l2 in query[l1]]
        print(f'.{len(querylist)}.')

        # run syncronious mass request
        time.sleep(1.0)
        response = multithreading(querylist, 16, 'bandcamp')

        # make nested list
        if not isinstance(response,list):
            response = [response]
        partition=[]
        i=0
        l = [len(query[q]) for q in query]
        for n in l:
            partition.append(response[i:i+n])
            i+=n

        qk = list(query.keys())
        print(f'.{len(response)}->{len(partition)}={len(qk)}.')
        for episode in range(len(qk)):

            qt = list(query[qk[episode]].keys())
            print(f'.{len(partition[episode])}={len(qt)}.',end='\r')

            for td in range(len(qt)):

                soup = bs(partition[episode][td], "html.parser")

                try:
                    if soup.select('.noresults-header'):
                        query[qk[episode]][qt[td]] = -1
                except:
                    query[qk[episode]][qt[td]]['artist'] = soup.select('.subhead')[0].text.replace('\n','').split('by')[1].strip()
                    query[qk[episode]][qt[td]]['title'] = soup.select('.heading')[0].text.replace('\n','').strip()
                    query[qk[episode]][qt[td]]['url'] = soup.select('.itemurl')[0].text.replace('\n','').strip()
                    break

        return(query)

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
        meta = self._j2d(f'./meta')

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
                    if name in meta:
                        doc += f"""<li><a class="show" href="./html/{name}.html">{how}</li>"""
                    else:
                        doc += f"""<li><a class="show">{how}</li>"""
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
        doc += f'<div><h2><a href="https://nts.live/shows/{show}">{title[show]}</a></h2><br><blockquote><a href="https://open.spotify.com/playlist/{pid}">⭕ : Playlist</a></blockquote></div>' # Show Title Spotify_icon.svg
        #⚫⚪ = Listen Back<br>🟢 = Spotify<br><img src="../assets/bandcamp-logo-alt.svg" class="icon"/> = Bandcamp<br>

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
                    bnd = f"""<a class="goto" href="{bc}"><img src="../assets/bandcamp-logo-alt.svg" class="subicon"/></a>  """
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

# END

# MULTITHREADING WORKER
from multiprocessing import Process

def multithreading(taskdict, no_workers,kind):

    stn = nts()
    stn.connect()
    global count, amount, taskcopy, c_lock
    count = 0
    c_lock = Lock()
    taskcopy = dict(taskdict)
    amount = len(taskdict)
    keys = list(taskdict.keys())[::-1]

    def counter(tid,result):
        global c_lock
        c_lock.acquire()
        taskdict[tid] = result
        keys.remove(tid)
        global count
        count += 1
        c_lock.release()
        return(count)

    def task(kind,taskid):
        global taskcopy
        if kind == 'spotify':
            result = stn._run(taskcopy[taskid])
            cont = counter(taskid,result)
        elif kind == 'rate':
            tn = True
            c = 0
            while tn:
                c += 1
                try:
                    a0,t0,r0,u0 = stn.test(taskcopy[taskid]['s'],taskcopy[taskid]['qa'],taskcopy[taskid]['qt'])
                    tn = False
                except:
                    print(f'[{c}/TF]',end='\r')
            cont = counter(taskid,{'a':a0,'t':t0,'r':r0,'u':u0})
        elif kind == 'bandcamp':
            time.sleep(1.0)
            result = stn.mt_request(taskcopy[taskid])
            cont = counter(taskid,result)
        
        return(cont)

    class __worker__(Thread):
        def __init__(self, request_queue):
            Thread.__init__(self)
            self.queue = request_queue
        def run(self): # def worker(workq):
            global amount
            while not self.queue.empty(): # while True:
                taskid = self.queue.get_nowait() #self.queue
                if not taskid:
                    if kind=='rate':
                        ''' EMERGENCY BREAK '''
                        global count
                        count = amount
                    break
                start = time.time()
                # TASK START
                cont = task(kind,taskid)
                # TASK END
                end = time.time()
                print(f"|{cont}/{amount}/{round(end - start,2)}|",end='\r')
                self.queue.task_done() #self.queue

    # Create queue and add tasklist
    workq = queue.Queue()
    for k in keys:
        workq.put(k)
    for _ in range(no_workers):
        workq.put("")

    # Create workers and add to the queue
    workers = []
    for _ in range(no_workers):
        worker = __worker__(workq)
        worker.start()
        workers.append(worker)


    if kind == 'rate':
        kill = False
        while not kill:
            time.sleep(10.0)
            print(f'({count})',end='\r')
            if count == amount:
                kill = True
        if keys:
            for taskid in keys:
                cont = task(kind,taskid)
    else:
        for worker in workers:
            worker.join()

    print('.Threading.Complete.',end='\r')
    return(taskdict)
#

