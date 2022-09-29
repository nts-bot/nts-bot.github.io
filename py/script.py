# BASIC LIBRARIES
import os, json, time, requests, re, pickle, urllib, sys, datetime
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
# SPOTIFY API TOOL
import spotipy
# MULTITHREADING TASKS
import queue
# IMAGE PROCESSING TOOLS
import cv2, base64
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
        self.meta = self._j2d(f'./meta')
        # try:
        #     self.meta = self._j2d(f'./meta')
        # except:
        #     print('META FILE CORRUPTED : USING BACKUP')
        #     self.meta = self._j2d(f'./extra/meta')

    # LOCAL DATABASE

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

    def prerun(self,json1,json2='',meta=''):
        js1 = self._j2d(json1)
        if json2:
            js2 = self._j2d(json2)
            if meta:
                js2 = js2[meta]
        #
        ok = [False]
        do = []
        #
        if json2:        
            for i in js1: # episodes
                if (i not in js2) and isinstance(js1[i],dict):
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
        else:
            for i in js1: # episodes
                if isinstance(js1[i],dict) and (not js1[i]):
                    ok += [True]
                    do += [i]
        #
        do = self.scene(do)
        if do:
            print(f'. . . . . . . . . . . . .{json1[2:5]}:{json2[2:5]}:{len(do)}.',end='\r')
        return(any(ok),do)

    # RUN SCRIPT

    def review(self,show):
        tday = datetime.date.today()
        day = [tday]
        for i in range(1,15):
            day += [tday - datetime.timedelta(i)]
        #
        try:
            rday = datetime.datetime.fromtimestamp(os.path.getmtime(f"./spotify/{show}.json")).date()
        except:
            print('.',end='\r')
            return(True)
        if rday in day:
            print('$',end='\r')
            return(True)
        else:
            print('%',end='\r')
            return(False)
            
    def runner(self,show,path,command):
        rq, do = self.prerun(f"./tracklist/{show}",path)
        if rq:
            print('!',end='\r')
            if command == 1:
                self.ntstracklist(show,do)
            elif command == 2:
                self.searchloop(show,['tracklist','spotify_search_results'],'search',do)
            elif command == 3:
                self.searchloop(show,['tracklist','spotify','spotify_search_results'],'rate',do)
            elif command == 4:
                self.searchloop(show,['tracklist','bandcamp_search_results','spotify'],'bandcamp',do)
            elif command == 5:
                self.searchloop(show,['tracklist','bandcamp','bandcamp_search_results'],'rate',do)
                self.mt_bmeta(show)
            elif command == 6:
                self.spotifyplaylist(show)


    def _reset(self,show):
        print('.RESET.')
        self._d2j(f"./spotify_search_results/{show}",dict())
        self._d2j(f"./spotify/{show}",dict())
        # self._d2j(f"./bandcamp_search_results/{show}",dict())
        # self._d2j(f"./bandcamp/{show}",dict())
        d = self._j2d(f"./uploaded")
        d[show] = dict()
        self._d2j(f"./uploaded",d)
        f = self._j2d(f"./extra/reset")
        f[show] = 1
        self._d2j(f"./extra/reset",f)

    def runscript(self,shows): #,bd=False,fast=False
        self.backup()
        self.connect()
        o = {i:shows[i] for i in range(len(shows))}
        print(o)
        for i in range(len(shows)):
            show = shows[i]
            # reset 
            if show not in self._j2d(f"./extra/reset"):
                self._reset(show)
            #
            oo = show + '. . . . . . . . . . . . . . . . . . . . . . . .'
            print(f'{oo[:50]}{i}/{len(shows)}')
            # SCRAPE / PRELIMINARY
            v = self.review(show)
            if v:
                self.scrape(show,True) # short
            else:
                self.scrape(show) # long
            # TRACKLIST
            self.runner(show,"",1)
            while True:
                try:
                    # SPOTIFY
                    self.runner(show,f"./spotify_search_results/{show}",2)
                    self.runner(show,f"./spotify/{show}",3)
                    # BANDCAMP
                    bd = False
                    if bd:
                        self.runner(show,f"./bandcamp_search_results/{show}",4)
                        self.runner(show,f"./bandcamp/{show}",5)
                    # ADD
                    if show not in self._j2d('./uploaded'):
                        self.spotifyplaylist(show)
                    else:
                        self.runner(show,f"./uploaded",6)
                    break
                except KeyboardInterrupt:
                    break
                except Exception as error:
                    print(error)
            # HTML
            # self.showhtml(show)
        _git()
        # self.home()

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
            print(f'{no_of_pagedowns:03}', end='\r')
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
        try:
            for i in grid[0]:
                a = i.select('a')
                if a:
                    href = a[0]['href']
                    episode = href.split('/episodes/')[1]
                    if episode not in episodelist.keys():
                        print(f'. . . . . . .{episode[-10:]}.', end='\r')
                        episodelist[episode] = dict()
                    else:
                        print(f'. . . . . . .{episode[-5:]}', end='\r')
                else:
                    print('href failed')

            # EPISODES META

            episodemeta = soup.select('.nts-grid-v2-item__content')
            try:
                x = self.meta[show]
            except KeyError:
                self.meta[show] = dict()
            for i in episodemeta:
                sub = i.select('.nts-grid-v2-item__header')[0]
                ep = sub['href'].split('/')[-1]
                date = sub.select('span')[0].text
                eptitle = sub.select('.nts-grid-v2-item__header__title')[0].text
                self.meta[show][ep] = {'title':eptitle,'date':date}
            self._d2j(f'./meta',self.meta)

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
                title = show
                desk = ''
            titlelist[show] = title
            desklist[show] = desk
                
            self._d2j('./extra/titles',titlelist)
            self._d2j('./extra/descriptions',desklist)
            self._d2j(f'./tracklist/{show}',episodelist)
        except Exception as error:
            print(f'Scrape Error : {error}')
        
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
        
        if show not in self.meta:
            self.meta[show] = dict()
        if not episodes:
            episodes = episodelist

        for episode in episodes:
            try:
                self.meta[show][episode]
            except:
                self.meta[show][episode] = dict()
            try:
                episodelist[episode]
            except:
                episodelist[episode] = dict()
            if (not episodelist[episode] and isinstance(episodelist[episode],dict)) or (not self.meta[show][episode]):
                print(f'{episode[:7]}{episode[-7:]}', end='\r')
                url = f"https://www.nts.live/shows/{show}/episodes/{episode}"
                soup = bs(self.req(url).content, "html.parser")
                if not episodelist[episode]:
                    print(f'{episode[:7]}{episode[-7:]}:soup', end='\r')
                    # try:
                    tracks = soup.select('.track')
                    for j in range(len(tracks)):
                        print(f'{episode[:7]}{episode[-7:]}:{j:02}', end='\r')
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
                    if not episodelist[episode]:
                        print(f'{episode[:7]}{episode[-7:]}:fail', end='\r')
                        episodelist[episode] = ''
                    self._d2j(f'./tracklist/{show}',episodelist)
                if (not self.meta[show][episode]):
                    print(f'{episode[:7]}{episode[-7:]}:meta', end='\r')
                    try:
                        bt = soup.select('.episode__btn')
                        date = bt[0]['data-episode-date']
                        eptitle = bt[0]['data-episode-name']
                        self.meta[show][episode] = {'title':eptitle,'date':date}
                    except:
                        try:
                            print(f'.trying-once-more-to-find-meta.')
                            soup = self.browse(url,1)
                            bt = soup.select('.episode__btn')
                            date = bt[0]['data-episode-date']
                            eptitle = bt[0]['data-episode-name']
                            self.meta[show][episode] = {'title':eptitle,'date':date}
                        except:
                            print(f'FAILURE PROCESSING META : {show}:{episode}\n')
                            self.meta[show][episode] = {'title':'','date':'00.00.00'}
                    self._d2j(f'./meta',self.meta)
            else:
                pass

    # SPOTIFY API

    @timeout(15.0)
    def subconnect(self,index,pick):
        ''' CONNECTION FUNCTION w/ TIMEOUT '''
        self.user = os.getenv("ssr")
        callback = 'http://localhost:8888/callback'
        cid = os.getenv(f"{index[pick]}id")
        secret = os.getenv(f"{index[pick]}st")
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
                            multiple[episode][trdx] = 0
                        elif kind == 'rate':
                            # 0 : TRACKLIST ; 1 : RATE ; 2 : SEARCH
                            multiple[episode][trdx] = 0
                        elif kind == 'bandcamp':
                            # 0 : TRACKLIST ; 1 : BANDCAMP ; 2 : RATE
                            multiple[episode][trdx] = 0
    
        if any([True for i in multiple if multiple[i]]):
            if kind == 'search':
                req = self.mt_spotifysearch(eval(jsonlist[0]),multiple)
            elif kind == 'rate':
                req = self.mt_spotifyrate(eval(jsonlist[0]),eval(jsonlist[2]),multiple)
            elif kind == 'bandcamp':
                req = self.mt_bandcamp(eval(jsonlist[0]),eval(jsonlist[2]),multiple)
            for episode in multiple:
                for td in multiple[episode]:
                    eval(jsonlist[1])[episode][td] = req[episode][td]
            self._d2j(f'./{jsonlist[1]}/{show}',eval(jsonlist[1]))

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
        except spotipy.SpotifyException:
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
            tr = True
            while tr:
                try:
                    ln = translator.detect(tex).lang
                    tr = False
                except:
                    time.sleep(1.0)
            if ln != 'en':
                tr = True
                c = 0
                while tr:
                    c += 1
                    try:
                        convert = translator.translate(tex,dest='en',src=ln).text
                        tr=False
                    except ValueError as error:
                        print(f'{ln} : {error}',end='\r')
                        tr=False
                        pass
                    except Exception:
                        print(f'{c}$',end='\r')
                        if c < 3:
                            time.sleep(1.0)
                        elif c < 6:
                            time.sleep(3.0)
                        elif c < 10:
                            time.sleep(5.0)
                        else:
                            time.sleep(10.0)
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
        Z1 = (X1 + Y1)/2

        G = list(map(set,[k1.split(' '),k2.split(' '),k3.split(' '),k4.split(' ')]))
        k1 = ' '.join(list(G[0]-G[2]-G[3]))
        k2 = ' '.join(list(G[1]-G[2]-G[3]))
        k3 = ' '.join(list(G[2]-G[0]-G[1]))
        k4 = ' '.join(list(G[3]-G[0]-G[1]))

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

        if not (x == 1 and y == 1):
            X1 = (X1 + min(x,y))/2
            Y1 = (Y1 + min(x,y))/2
            Z1 = (Z1 + min(x,y))/2

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

    # SPOTIFY PLAYLIST FUNCTIONS

    def scene(self,sequence):
        ''' GET UNIQUE ITEMS IN LIST & IN ORDER '''
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def spotifyplaylist(self,show,threshold=[3,10],reset=False):
        ''' APPEND/CREATE/REMOVE FROM SPOTIFY PLAYLIST '''
        pid = self.pid(show)
        meta = self.meta[show]
        sortmeta = sorted(['.'.join(value['date'].split('.')[::-1]),key] for (key,value) in meta.items())
        #
        uploaded = self._j2d(f'./uploaded')
        #
        if show not in uploaded:
            uploaded[show] = dict()
            reset = True
        elif (sortmeta) and (uploaded[show]):
            metacopy = [i[1] for i in sortmeta]
            met0 = list(uploaded[show].keys())
            for i in met0[:-1]:
                metacopy.remove(i)
            metaind = metacopy.index(met0[-1])
            met1 = metacopy[:metaind] # old shows
            if met1:
                uploaded[show] = dict() # reset upload
                reset = True
        #
        tid = []
        trackdict = dict()
        pup = []
        mis = 0
        almost = 0
        unsure = 0

        f = True
        ff = 0
        while f:
            fp = sortmeta[ff][0].split('.')
            firstep = f"{fp[2]}.{fp[1]}.{fp[0]}"
            if firstep != '00.00.00':
                f = False
            else:
                ff += 1
        lp = sortmeta[-1][0].split('.')
        lastep = f"{lp[2]}.{lp[1]}.{lp[0]}"

        showlist = self._j2d(f'./tracklist/{show}')
        rate = self._j2d(f'./spotify/{show}')
        upend = False
        for mt in sortmeta[::-1]:
            ep = mt[1]
            trackdict[ep] = []
            if ep not in uploaded[show]:
                uploaded[show][ep] = 1
                up = True
            else:
                up = False
            if showlist[ep]:
                for tr in rate[ep]:
                    #
                    ua = ' '.join(re.sub( r"([A-Z\d])", r" \1", rate[ep][tr]['artist']).split()).lower()
                    ut = ' '.join(re.sub( r"([A-Z\d])", r" \1", rate[ep][tr]['title']).split()).lower()
                    if ('unknown artist' in ua) or ('unknown' == ua) or ('unknown' == ut):
                        rate[ep][tr]["ratio"] = -1
                        rate[ep][tr]["uri"] = ''
                    #
                    if threshold[0] <= rate[ep][tr]['ratio'] <= threshold[1]:
                        tid += [rate[ep][tr]['trackid']]
                        if up:
                            upend = True
                            trackdict[ep] += [rate[ep][tr]['trackid']]
                    pup += [rate[ep][tr]['trackid']]
                    if not rate[ep][tr]['trackid']:
                        mis += 1
                    if threshold[0]  <= rate[ep][tr]['ratio'] == 4:
                        almost += 1
                    if threshold[0]  <= rate[ep][tr]['ratio'] <= 3:
                        unsure += 1

        self._d2j(f'./spotify/{show}',rate)
        tidup = self.scene(tid[::-1])[::-1]
        dups = len(tid) - len(tidup)

        if reset:
            current = self.sp.user_playlist_tracks(self.user,pid)
            tracks = current['items']
            while current['next']:
                current = self.sp.next(current)
                tracks.extend(current['items'])        
            ids = []
            for x in tracks:
                ids.append(x['track']['id'])
            rem = list(set(ids))
            hund = [rem[i:i+100] for i in range(0, len(rem), 100)]
            for i in hund:
                print(f'.resetting',end='\r')
                self.sp.user_playlist_remove_all_occurrences_of_tracks(self.user, pid, i)

        if upend:
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
        x_test = self.sp.user_playlist_change_details(self.user,pid,name=f"{title} - NTS",description=f"{syn}")
        x_real = self.sp.user_playlist_change_details(self.user,pid,name=f"{title} - NTS",description=f"{desk.split('.')[0]}... {syn}")

        self._d2j(f'./uploaded',uploaded)

    def follow(self,kind='cre'):
        ''' SECONDARY SPOTIFY USERS WHO MAINTAIN ALPHABETICALLY ORGANIZED PLAYLISTS BELOW SPOTIFY (VISIBLE) PUBLIC PLAYLIST LIMIT (200) '''
        creds = self._j2d(f'{kind}dentials')
        usrcall = round(len(self.showlist)/200 + 0.4999)
        for us in range(usrcall):
            usr = us + 1
            user = creds[str(usr)]['user']
            cid = creds[str(usr)]['cid']
            secret = creds[str(usr)]['secret']
            callback = 'http://localhost:8888/callback'
            spot = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=cid,client_secret=secret,redirect_uri=f"{callback}",scope='playlist-modify-public user-follow-modify',username=user), requests_timeout=5, retries=5)
            print('Testing .',end=' ')
            test = spot.user(user)
            print('Successful .',end=' ')
            
            if kind == 'cre':
                extent = self.showlist[(200 * (usr - 1)):(200 * (usr))]

            print('Unfollowing',end='\r')
            cn = False
            while not cn:
                try:
                    plys = []
                    for i in range(4):
                        it = spot.user_playlists(user,offset=(i * 50))['items']
                        plys += [k['id'] for k in it]
                    for i in plys:
                        playlist_owner_id = '31yeoenly5iu5pvoatmuvt7i7ksy'
                        spot.user_playlist_unfollow(playlist_owner_id, i)
                    cn = True
                except:
                    print('error')

            print('Following')
            print(f'{extent[0][0]} : {extent[-1][0]}')
            cn = False
            while not cn:
                try:
                    for i in extent[::-1]:
                        print(i[:20],end='\r')
                        playlist_owner_id = '31yeoenly5iu5pvoatmuvt7i7ksy'
                        playlist_id = self.pid(i)
                        if playlist_id:
                            spot.user_playlist_follow_playlist(playlist_owner_id, playlist_id)
                        else:
                            print(f'FAILED : {i}')
                    cn = True
                except:
                    print('error')
            

            del creds[str(usr)]
            u = []
            for i in creds:
                u += [creds[i]['user']]
            spot.user_follow_users(u)

    # MULTITHREADING FUNCTIONS

    def qmt(self,q,kind,nw=16):
        q1 = q[0]
        taskdict = {f"q1.{l1:03}.{l2:03}":q1[list(q1.keys())[l1]][list(q1[list(q1.keys())[l1]].keys())[l2]] 
                    for l1 in range(len(q1)) 
                    for l2 in range(len(q1[list(q1.keys())[l1]]))
                    }
        if len(q) == 2:
            q2 = q[1]
            taskdict |= {f"q2.{l1:03}.{l2:03}":q2[list(q2.keys())[l1]][list(q2[list(q2.keys())[l1]].keys())[l2]] 
                        for l1 in range(len(q2)) 
                        for l2 in range(len(q2[list(q2.keys())[l1]]))
                        }
        return(multithreading(taskdict, nw, kind))

    def mt_request(self,content):
        c = 0
        request = urllib.request.Request(content)
        repeat = True
        while repeat:
            try:
                c+=1
                return(urllib.request.urlopen(request).read())
                repeat = False
            except:
                print(f'{c}$',end='\r')
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
        taskdict = self.qmt([q1,q2],'spotify')
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
                if taskdict[f"q2.{l1:03}.{l2:03}"]['tracks']['items']: # q2
                    S1 = [{'artist':j['artists'][0]['name'],
                        'title':j['name'],
                        'uri':j['uri'].split(':')[-1]} 
                        for j in taskdict[f"q2.{l1:03}.{l2:03}"]['tracks']['items'][:3]]
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
        taskdict = self.qmt([q1,q2],'rate',8)
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

                    if round(eval(f'r{dx}'),1) >= 0.9:
                        lag = 6
                    elif round(eval(f'r{dx}'),1) >= 0.8:
                        lag = 5
                    elif round(eval(f'r{dx}'),1) >= 0.6:
                        lag = 3
                    elif round(eval(f'r{dx}'),1) >= 0.7:
                        lag = 4
                    elif round(eval(f'r{dx}'),1) >= 0.5:
                        lag = 2
                    elif round(eval(f'r{dx}'),1) >= 0.4:
                        lag = 1
                    else: # round(eval(f'r{dx}'),1) < 0.4
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
        return(self.mt_camp(q1,q2))

    def mt_camp(self,q1,q2):
        taskdict = self.qmt([q1],'bandcamp',8)
        q12 = dict()
        for l1 in range(len(q1)):
            episode = list(q1.keys())[l1]
            for l2 in range(len(q1[list(q1.keys())[l1]])): # td are tracks
                td = list(q1[list(q1.keys())[l1]].keys())[l2]
                if taskdict[f"q1.{l1:03}.{l2:03}"] == '':
                    if episode not in q12:
                        q12[episode] = dict()
                    q12[episode][td] = q2[episode][td]
                else:
                    q1[episode][td] = {'s0':taskdict[f"q1.{l1:03}.{l2:03}"],'s1':''}
        if q12:
            print('.running-twice.',end='\r')
            td2 = self.qmt([q12],'bandcamp',8)
            for l1 in range(len(q12)):
                episode = list(q12.keys())[l1]
                for l2 in range(len(q12[list(q12.keys())[l1]])): # td are tracks
                    td = list(q12[list(q12.keys())[l1]].keys())[l2]
                    q1[episode][td] = {'s0':'','s1':td2[f"q1.{l1:03}.{l2:03}"]}
                    
        return(q1)

    def mt_bmeta(self,show):
        bandcamp = self._j2d(f'./bandcamp/{show}')
        q1 = dict()
        for e in bandcamp:
            for t in bandcamp[e]:
                if bandcamp[e][t]['ratio'] >= 3:
                    if 'albumid' not in bandcamp[e][t]:
                        if e not in q1:
                            q1[e] = dict()
                        q1[e][t] = bandcamp[e][t]['trackid']
        if q1:
            taskdict = self.qmt([q1],'bmeta',16) #8?
            for l1 in range(len(q1)):
                episode = list(q1.keys())[l1]
                for l2 in range(len(q1[list(q1.keys())[l1]])): # td are tracks
                    td = list(q1[list(q1.keys())[l1]].keys())[l2]
                    bandcamp[episode][td]['album_id'] = taskdict[f"q1.{l1:03}.{l2:03}"]['album_id']
                    bandcamp[episode][td]['track_id'] = taskdict[f"q1.{l1:03}.{l2:03}"]['track_id']
        self._d2j(f'./bandcamp/{show}',bandcamp)

    # HTML MAKER

    def home(self):
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
            <script>
                    function embedplay(link) 
                    {
                        document.getElementById("embed").setAttribute('src', link)
                        document.querySelector('[title="Play"]').click()
                    }
            </script>
            </head>
            <body>
                <h1><a href="https://github.com/nts-bot/nts-bot.github.io">GitHub</a></h1>
            """
        pid = self._j2d('pid')[show]
        title = self._j2d('./extra/titles')
        # <div><br>
        # <a href="https://open.spotify.com/playlist/{pid}"><img class="picon" src="../assets/Spotify_icon.svg.png"/></a>
        # </div>
        doc += f"""
        <div>
        <h2><a href="https://nts.live/shows/{show}">{title[show]}</a></h2><br>
        <iframe id="embed" style="border-radius:12px" src="https://open.spotify.com/embed/playlist/{pid}?utm_source=generator" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy" seamless>
        </iframe>
        </div>
        """
        episodes = self._j2d(f'./tracklist/{show}')
        spotify = self._j2d(f'./spotify/{show}')
        bandcamp = self._j2d(f'./bandcamp/{show}')
        meta = self._j2d(f'./meta')[show]
        sortmeta = sorted(['.'.join(value['date'].split('.')[::-1]),key] for (key,value) in meta.items())

        for mt in sortmeta[::-1]:

            i = mt[1]
            ti = f"{meta[i]['title']} - {meta[i]['date']}"

            doc += f'<details><summary><h3><div class="title">{ti}</div><span class="data"><a href="https://nts.live/shows/{show}/episodes/{i}"><img class="icon" src="../assets/nts-icon.jpg"/></a></span></h3></summary>'
            doc += '<ol>'

            for j in episodes[i]:

                tart = episodes[i][j]['artist']
                ttit = episodes[i][j]['title']

                try:
                    tid = bandcamp[i][j]['track_id']
                    aid = bandcamp[i][j]['album_id']
                    if aid == "null":
                        bc = f'https://bandcamp.com/EmbeddedPlayer/track={tid}/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/artwork=small/transparent=true/'
                    else:
                        bc = f'https://bandcamp.com/EmbeddedPlayer/album={aid}/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/artwork=small/track={tid}/transparent=true/'
                    bnd = f"""
                    <button class="goto" onClick="embedplay('{bc}')">
                    <img src="../assets/bandcamp-logo-alt.svg" class="subicon"/>
                    </button>
                    """
                except:
                    bnd = ''
                
                try:
                    if spotify[i][j]['ratio'] >= 3:
                        spo = f"""
                        <button class="goto" onClick="embedplay('https://open.spotify.com/embed/track/{spotify[i][j]['trackid']}?utm_source=generator')">
                        <img class="picon" src="../assets/Spotify_icon.svg.png"/>
                        </button>  
                        """
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

    # BACKUP

    def backup(self):
        for i in ['meta','pid']:
            file = self._j2d(f'./{i}')
            self._d2j(f'./extra/{i}',file)


# MULTITHREADING WORKER

def multithreading(taskdict, no_workers,kind):

    stn = nts()
    stn.connect()
    global count, wcount
    count = 0
    wcount = 0
    c_lock = Lock()
    taskcopy = dict(taskdict)
    amount = len(taskdict)
    keys = list(taskdict.keys())[::-1]

    def counter(tid,result,thr=True):
        if thr:
            c_lock.acquire()
        try:
            keys.remove(tid)
            taskdict[tid] = result
        except:
            pass
        global count
        count += 1
        if thr:
            c_lock.release()
        return(count)

    def task(kind,taskid):
        if kind == 'spotify':
            result = stn._run(taskcopy[taskid])
            cont = counter(taskid,result)
        elif kind == 'rate':
            tn = True
            p = 0
            while tn:
                try:
                    p += 1
                    a0,t0,r0,u0 = stn.test(taskcopy[taskid]['s'],taskcopy[taskid]['qa'],taskcopy[taskid]['qt'])
                    tn = False
                except:
                    print(error,end='\r')
                    pass
            cont = counter(taskid,{'a':a0,'t':t0,'r':r0,'u':u0})
        elif kind == 'bandcamp':
            time.sleep(1.0)
            result = stn.mt_request(taskcopy[taskid])
            soup = bs(result, "html.parser")
            if soup.select('.noresults-header'):
                cont = counter(taskid,'') #-1
            else:
                d = []
                kk = len(soup.select('.subhead'))
                if kk <= 3:
                    kr = kk
                else:
                    kr = 3
                for k in range(kr):
                    d += [{'artist':soup.select('.subhead')[k].text.replace('\n','').split('by')[1].strip(),
                    'title':soup.select('.heading')[k].text.replace('\n','').strip(),
                    'uri':soup.select('.itemurl')[k].text.replace('\n','').strip()}]
                cont = counter(taskid,d)
        elif kind == 'bmeta':
            soup = str(stn.mt_request(taskcopy[taskid]))
            cont = counter(taskid,{
                'album_id':re.findall(f'album_id&quot;:(.*?),',soup)[1],
                'track_id':re.findall(f'track_id&quot;:(.*?),',soup)[0]})
        return(cont)

    class __worker__(Thread):
        def __init__(self, request_queue):
            Thread.__init__(self)
            self.queue = request_queue
        def run(self):
            while not self.queue.empty():
                taskid = self.queue.get_nowait()
                if not taskid:
                    break
                start = time.time()
                # TASK START
                cont = task(kind,taskid)
                # TASK END
                end = time.time()
                print(f"|{cont}/{amount}/{round(end - start,2)}|",end='\r')
                self.queue.task_done()

    # Create queue and add tasklist
    workq = queue.Queue()
    for k in keys:
        workq.put(k)
    for _ in range(no_workers):
        workq.put("")
    #        
    workers = []
    for _ in range(no_workers):
        worker = __worker__(workq)
        worker.start()
        workers.append(worker)

    if kind == 'rate':
        kill = False
        try:
            while not kill:
                time.sleep(5.0)
                print(f'({count})',end='\r')
                if count >= amount:
                    kill = True
                elif count + 10 >= amount:
                    x = 0
                    while x < 10:
                        x += 2
                        time.sleep(round(x/2))
                        if count + x/2 >= amount:
                            break
                    kill = True
                    sys.exit()
        except SystemExit:
            print('.double-checking.')
            for taskid in taskcopy:
                if taskcopy[taskid] == taskdict[taskid]:
                    tn = True
                    while tn:
                        try:
                            a0,t0,r0,u0 = stn.test(taskcopy[taskid]['s'],taskcopy[taskid]['qa'],taskcopy[taskid]['qt'])
                            tn = False
                        except Exception as error:
                            pass
                    cont = counter(taskid,{'a':a0,'t':t0,'r':r0,'u':u0},False)
    else:
        for worker in workers:
            worker.join()

    print('.Threading.Complete.',end='\r')
    return(taskdict)

# GIT PUSH

import git
def _git():
    try:
        repo = git.Repo(os.getenv("directory"))
        repo.git.add('.') #update=True
        repo.index.commit("auto-gitpush")
        origin = repo.remote(name='origin')
        origin.push()
    except Exception as error:
        print(f'Error : {error}')  

# END
