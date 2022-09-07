'''
HERE WE WILL WEBSCRAPE BANDCAMP FOR TRACKS AND FROM THE RESULTS, CREATE A JSON FILE THAT RECORDS SEARCH RESULTS & COMPARISON/ACCURACY TO ORIGINAL/QUERY
//
NEXT, WE WILL AUTOMATICALLY CREATE PLAYLISTS VIA THE TOOL https://bndcmpr.co
'''

# Libraries
import os, requests, urllib, pickle, time
from requests.exceptions import ConnectionError
# Browser (if Javascript)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
# Html Parser
from bs4 import BeautifulSoup as bs
# String Comparison
from difflib import SequenceMatcher
# Unicode Conversion
from unidecode import unidecode
# PRE-INIT
from dotenv import load_dotenv
load_dotenv()
# LOAD LOCAL API CLASS FILE
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import api
ipa = api.api()

class nts:

    def __init__(self):
        pass

    ''' [1] WEBSCRAP BANDCAMP & SAVE RESULT '''

    def ratio(self,a,b):
        ''' GET SIMILARITY RATIO BETWEEN TWO STRINGS '''
        return(SequenceMatcher(None, self.refine(a), self.refine(b)).ratio())

    def req(self,url):
        i=0
        while i < 30:
            try:
                res = requests.get(url)
                return(res)
            except ConnectionError:
                print('Connection Error')
                time.sleep(1.0)
                i += 1

    def refine(self,text):
        text = text.replace('・',' ').replace('+',' ').replace(']',' ').replace('[',' ').replace(')',' ').replace('(',' ').replace('\n','').replace('\'',' ').replace('\"',' ').replace('-',' ').replace('!',' ').replace('/',' ').replace(';',' ').replace('selections','').replace('with ','').replace('medley','').replace('vocal','').replace('previously unreleased','').replace('remastering','').replace('remastered','').replace('various artists','').replace('vinyl','').replace('from','').replace('theme','').replace('motion picture soundtrack','').replace('soundtrack','').replace('full length','').replace('original','').replace('version','').replace('feat.','').replace('comp.','').replace('vocal','').replace('instrumental','').replace('&','and').replace('excerpt','').replace('single','').replace('album','').replace('anonymous','').replace('unknown','').replace('traditional','')
        for i in list(range(1990,2022)):
            text = text.replace(str(i),'').replace('  ',' ')
        return(text.strip())

    def search(self,show):

        shelf = ipa._j2d(f'./json/{show}')
        flags = ipa._j2d(f'./bandcamp/{show}')
        
        c = 0
        for episode in shelf:
            c += 1
            print(f'. . . . . . . . . . . . . . . . .{c}:{len(list(shelf.keys()))}.',end='\r')
            try:
                flags[episode]
            except KeyError:
                flags[episode] = dict()

            if list(set(shelf[episode].keys())-set(flags[episode].keys())):
                print(f'{episode[:10]}:{episode[-10:]}',end='\r')

                for trdx in shelf[episode]:
                    if (trdx not in flags[episode]): 

                        ort = shelf[episode][trdx]["artist"] # original artist
                        oit = shelf[episode][trdx]["title"] # original title

                        track = f'{ort} {oit}'

                        quer1 = urllib.parse.quote(track)
                        quer2 = urllib.parse.quote(self.refine(unidecode(track)))
                        tracks = []

                        try:
                            url = f"https://bandcamp.com/search?q={quer1}&item_type=t"
                            soup = bs(self.req(url).content, "html.parser")
                            tl = []
                            tracks = soup.select('.data-search')
                        except:
                            try:
                                url = f"https://bandcamp.com/search?q={quer2}&item_type=t"
                                soup = bs(self.req(url).content, "html.parser")
                                tl = []
                                tracks = soup.select('.data-search')
                            except:
                                pass

                        for i in tracks[:3]:
                            tj = dict()
                            try:
                                art = i.select('.subhead')[0].text.replace('\n','').split('by')[1]
                                tit = i.select('.heading')[0].text.replace('\n','').strip()

                                A = max([self.ratio(art,ort), self.ratio(ort,art), self.ratio(art,oit), self.ratio(oit,art)])
                                T = max([self.ratio(tit,ort), self.ratio(ort,tit), self.ratio(tit,oit), self.ratio(oit,tit)])

                                if (A + T)/2 > 0.7:    
                                    tj['artist'] = art
                                    tj['title'] = tit
                                    tj['url'] = i.select('.itemurl')[0].text.replace('\n','')
                                    tl += [tj]
                            except:
                                pass

                        if tl:
                            flags[episode][trdx] = tl[0]
                        else:
                            flags[episode][trdx] = dict()

                        ipa._d2j(f'./bandcamp/{show}',flags)

    def run_search(self):
        with open(f'./extra/bait.pickle', 'wb') as handle:
            pickle.dump(0, handle, protocol=pickle.HIGHEST_PROTOCOL)
        flag = ipa._j2d('./extra/blag')
        showlist = [x for x in ipa.showlist if x not in flag]


        if len (showlist) > 40:
            print('sublist')
            ipa.wait('flg',True)
            with open('./extra/flag.pickle', 'rb') as handle:
                pick = pickle.load(handle)
            pick += 1
            lim = 20
            if pick >= lim:
                pick = 0
            with open('./extra/flag.pickle', 'wb') as handle:
                pickle.dump(pick, handle, protocol=pickle.HIGHEST_PROTOCOL)
            sublist = showlist[pick::lim]
            print(f'\ncurrent Pickle : {pick}\n')
            ipa.wait('flg',False)
        else:
            sublist = showlist

        par = {str(m) : sublist[m] for m in range(len(sublist))}
        print(par)

        for show in sublist:
            print(show)
            self.search(show)
            ipa.flag(show,True,'blag','bait')

    ''' [2] IF URL ; CREATE/UPDATE BANDCAMP PLAYLIST '''

    def login(self):
        print('.login.',end='\r')
        url = 'https://bndcmpr.co/'

        options = webdriver.ChromeOptions() 
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.headless = True
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options) #

        driver.get(url)
        time.sleep(1.0)

        # LOGIN FORM

        # Username
        v1 = '//*[@id="app"]/div/div[1]/div[1]/input[1]'
        driver.find_element(By.XPATH, v1).click()
        driver.find_element(By.XPATH, v1).send_keys("NTSbot")
        # Password
        v2 = '//*[@id="app"]/div/div[1]/div[1]/input[2]'
        driver.find_element(By.XPATH, v2).click()
        p = os.getenv("bndcmpr")
        driver.find_element(By.XPATH, v2).send_keys(p)
        # Login
        v3 = '//*[@id="app"]/div/div[1]/div[1]/a[1]'
        driver.find_element(By.XPATH, v3).click()

        timeout = 10
        try:
            element = EC.element_to_be_clickable((By.CLASS_NAME, 'playlist-creator'))
            WebDriverWait(driver, timeout).until(element)
        except TimeoutException:
            raise TimeoutError("Timeout")

        print('.logged in.',end='\r')

        return(driver)

    def playlist(self,show):

        driver = self.login()

        # PLAYLIST

        titlepath = '//*[@id="app"]/div/div[2]/div[2]/div[1]/input' #title # //*[@id="app"]/div/div[2]/div[2]/div[1]/input
        deskpath = '//*[@id="app"]/div/div[2]/div[2]/div[1]/textarea' #description
        trackpath = '//*[@id="app"]/div/div[2]/div[2]/div[3]/div/input' # track
        addpath = '//*[@id="app"]/div/div[2]/div[2]/div[3]/div/a' # add track button 
        makepath = '//*[@id="app"]/div/div[2]/div[2]/div[4]' # create/update playlist
        editpath = '//*[@id="app"]/div/div[2]/div[2]/div/h2[2]/a[1]' # edit playlist
        tracklistpath = '//*[@id="app"]/div/div[2]/div[2]/div[2]/div'

        ## Check bid.json

        pid = ipa._j2d('bid')
        try:
            bid = pid[show]
        except KeyError:
            bid = ''

        if not bid: # create playlist

            # CREATE PLAYLIST
            title, desk = ipa.bio(show)
            desk = desk.replace('\n',' ').replace('\\','').strip()
            desk = f'[www.nts.live/shows/{show}] {desk}'
            # title
            driver.find_element(By.XPATH, titlepath).click()
            driver.find_element(By.XPATH, titlepath).send_keys(title)
            # description
            driver.find_element(By.XPATH, deskpath).click()
            driver.find_element(By.XPATH, deskpath).send_keys(desk)
            time.sleep(1.0)
            
        else: # update playlist
            driver.get(f'https://bndcmpr.co/{bid}')
            time.sleep(1.0)
            driver.find_element(By.XPATH, editpath).click()
            time.sleep(1.0)

        # UPDATE TRACKS

        shelf = ipa._j2d(f'./bandcamp/{show}')
        flags = ipa._j2d(f'./bndcmpr/{show}')

        c = 0
        m = []
        for episode in shelf:
            c += 1
            print(f'. . . . . . . . . . . . . . . . .{c}:{len(list(shelf.keys()))}.',end='\r')
            try:
                flags[episode]
            except KeyError:
                flags[episode] = dict()

            if list(set(shelf[episode].keys())-set(flags[episode].keys())):
                print(f'{episode[:10]}:{episode[-10:]}',end='\r')

                for trdx in shelf[episode]:
                    if (trdx not in flags[episode]): 

                        if shelf[episode][trdx]:
                            print('. . . . . . .adding.tracks.',end='\r')
                            timeout = 10
                            try:
                                element = EC.element_to_be_clickable((By.CLASS_NAME, 'track-input'))
                                WebDriverWait(driver, timeout).until(element)
                            except TimeoutException:
                                raise TimeoutError("Timeout")
                            oldlength = len(driver.find_elements(By.XPATH, tracklistpath))
                            driver.find_element(By.XPATH, trackpath).click()
                            driver.find_element(By.XPATH, trackpath).send_keys(shelf[episode][trdx]['url'])
                            time.sleep(0.5)
                            driver.find_element(By.XPATH, addpath).click()
                            time.sleep(1.0)
                            newlength = len(driver.find_elements(By.XPATH, tracklistpath))
                            while not (newlength == oldlength + 1):
                                print(f'. . . . . . .waiting.{newlength}={oldlength}',end='\r')
                                time.sleep(0.1)
                                newlength = len(driver.find_elements(By.XPATH, tracklistpath))
                            print('. . . . . . .track.added.',end='\r')
                            flags[episode][trdx] = 1
                            m += [True]
                        else:
                            flags[episode][trdx] = ''
                            m += [False]
                    else:
                        print('. . . . . .skipep.',end='\r')

        #

        driver.find_element(By.XPATH, makepath).click()
        # wait until playlist is made


        if any(m):
            print(f'CREATING PLAYLIST',end='\r')
            time.sleep(1.0)
            query = driver.current_url.split('/')[-1]
            while not (len(query) == 8):
                print(f'WAITING FOR PLAYLIST TO BE CREATED : CURRENT ID = {query}',end='\r')
                time.sleep(1.0)
                query = driver.current_url.split('/')[-1]
            #
            pid[show] = query
        else:
            print(f'NO BANDCAMP TRACKS FOUND for : {show}')
            pid[show] = ''
        ipa._d2j('bid',pid)
        time.sleep(1.0)
        ipa._d2j(f'./bndcmpr/{show}',flags)
        driver.quit()

    def run_playlist(self):
        bid = ipa._j2d('bid')
        for show in ipa.showlist:
            if show not in bid:
                print(show)
                self.playlist(show)
                ipa.flag(show,True,'galb','bait')

    def run(self):
        bid = ipa._j2d('bid')
        galf = ipa._j2d('./extra/galf')
        sublist = [x for x in ipa.showlist if x in galf]
        for show in sublist:
            print(show)
            self.search(show)
            if show not in bid:
                self.playlist(show)
                ipa.flag(show,True,'galb','bait')
                ipa.html()

    def reset(self):
        driver = self.login()
        bid = ipa._j2d('bid')
        
        for i in list(bid.keys())[::-1]:
            print(i,end='\r')

            if bid[i]:
                driver.get(f'https://bndcmpr.co/{bid[i]}')
                time.sleep(1.0)

                timeout = 20
                try:
                    element = EC.presence_of_element_located((By.CSS_SELECTOR, ".owner-controls"))
                    WebDriverWait(driver, timeout).until(element)
                except TimeoutException:
                    raise TimeoutError("Timeout")

                v1 = '//*[@id="app"]/div/div[2]/div[2]/div/h2[2]/a[2]' # delete playlist 
                driver.find_element(By.XPATH, v1).click()
                time.sleep(1.0)

                v2 = '//*[@id="app"]/div/div[2]/div[1]/div/a[1]' #confirm

                ext = False
                while not ext:
                    try:
                        print('. . . . . . . . . . . deleting.',end='\r')
                        driver.find_element(By.XPATH, v2).click()
                        ext = True
                    except:
                        pass

                ext = False
                while not ext: # wait for redirect to home page
                    try:
                        try:
                            v1 = '//*[@id="app"]/div/div[2]/div[2]/div[1]/input' #title
                            driver.find_element(By.XPATH, v1).click()
                        except:
                            v1 = '//*[@id="app"]/div/div[2]/div[3]/div[1]/input' #title
                            driver.find_element(By.XPATH, v1).click()
                        ext = True
                    except:
                        pass

                print('. . . . . . . . . . . deleted.',end='\r')
            else:
                pass

            del bid[i]
            ipa._d2j('bid',bid)


#