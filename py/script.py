
# Inbuilt Libraries
import os, json, time, requests, re, pickle, urllib
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

class nts:

    def __init__(self):
        dr = os.getenv("directory")
        os.chdir(f"{dr}")
        self.showlist = [i.split('.')[0] for i in os.listdir('./tracklist/')]

    # LOCAL DATABASE
    @timeout(20.0)
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
            time.sleep(1.0)
            return(self._j2d(path))
        
    @timeout(20.0)
    def _d2j(self,path,allot):
        try:
            if isinstance(allot,dict):
                with open(f"{path}.json", 'w', encoding='utf-8') as f:
                    json.dump(allot, f, sort_keys=True, ensure_ascii=False, indent=4)
            else:
                raise ValueError(f'You are trying to dump {type(allot)} instead dict()')
        except:
            print(f'Error When Storing JSON')
            time.sleep(1.0)
            self._d2j(path,allot)

    def prerun(self,json1,json2,tracks=True):
        js1 = self._j2d(json1)
        js2 = self._j2d(json2)
        ok = [False]
        for i in js1: # episodes
            if i not in js2:
                ok += [True]
            else:
                if tracks:
                    for j in js1[i]: # tracks
                        if j not in js2[i]:
                            ok += [True]
                        else:
                            ok += [False]
        return(any(ok))

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

    def scrape(self,show,short=False):
        url = f"https://www.nts.live/shows/{show}"
        if short:
            soup = bs(self.req(url).content, "html.parser")
        else:
            soup = self.browse(url)
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
        meta = self._j2d(f'./extra/meta')
        for i in episodemeta:
            sub = i.select('.nts-grid-v2-item__header')[0]
            ep = sub['href'].split('/')[-1]
            date = sub.select('span')[0].text
            eptitle = sub.select('.nts-grid-v2-item__header__title')[0].text
            try:
                store = meta[show]
            except KeyError:
                meta[show] = dict()
                store = meta[show]
            store[ep] = {'title':eptitle,'date':date}

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
        self._d2j(f'./extra/meta',meta)

    @timeout(5.0)
    def req(self,url):
        try:
            res = requests.get(url)
            return(res)
        except ConnectionError:
            print('Connection Error')
            time.sleep(1.0)
            self.req(url)

    def ntstracklist(self,show):
        episodelist = self._j2d(f'./tracklist/{show}')
        for episode in episodelist:
            if episodelist[episode]:
                pass
            elif isinstance(episodelist[episode],dict) and not episodelist[episode]:
                print(episode[:10], end='\r')
                url = f"https://www.nts.live/shows/{show}/episodes/{episode}"
                soup = bs(self.req(url).content, "html.parser")
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

    def flag(self,show,flag=True,title='flag',pick='wait'):
        self.wait(pick,True)
        flagger = self._j2d(f'./extra/{title}')
        try:
            flagger[show]
        except KeyError:
            flagger[show] = dict()
        if flag:
            flagger[show] = 1
        else:
            del flagger[show]
        self._d2j(f'./extra/{title}',flagger)
        self.wait(pick,False)

    # SPOTIFY SEARCH

    def pid(self,show):
        ''' GET/CREATE SHOW PLAYLIST ID '''
        pid = self._j2d('pid')
        try:
            shelf = pid[show]
            return(shelf)
        except KeyError: # new show
            tim = self._j2d('./extra/srch')
            tim[show] = 1
            self._d2j('./extra/srch',tim)
            #
            ref = self.sp.user_playlist_create(self.user,f'{show}-nts',public=True,description=f"(https://www.nts.live/shows/{show})")
            pid[show] = ref['id']
            self._d2j('pid',pid)
            return(ref['id'])

    def searchloop(self,show,jsonlist):

        for jsondir in jsonlist:
            locals()[jsondir] = self._j2d(f'./{jsondir}/{show}')

        counter = 0
        for episode in tracklist:
            store = False
            counter += 1
            print(f'{show[:7]}{episode[:7]}. . . . . . . . . .{counter}:{len(list(tracklist.keys()))}.',end='\r')
            

    # HTML

#