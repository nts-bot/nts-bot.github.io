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
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import spotify
spo = spotify.nts()

class nts:

    def __init__(self):
        pass

    ''' [1] WEBSCRAP BANDCAMP & SAVE RESULT '''

    def ratio(self,a,b):
        ''' GET SIMILARITY RATIO BETWEEN TWO STRINGS '''
        return(SequenceMatcher(None, self.refine(a,True), self.refine(b,True)).ratio())

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

    def kill(self,text):
        ''' ELIMINATE DUPLICATES & UNNECESSARY CHARACTERS WITHIN STRING '''
        cv = text.replace('・',' ').replace('+',' ').replace(']',' ').replace('[',' ').replace(')',' ').replace('(',' ').replace('\'',' ').replace('\"',' ').replace('-',' ').replace('!',' ').replace('/',' ').replace(';',' ').replace(':',' ').replace('.',' ').replace(',',' ').split(' ')
        return(" ".join(dict.fromkeys(cv)))

    def refine(self,text,kill=False):
        ''' ELIMINATE UNNECCESARY WORDS WITHIN STRING '''
        if kill:
            text = self.kill(text)
        for i in list(range(1990,2022)):
            text = text.replace(str(i),'')
        text = text.replace('selections','').replace('with ','').replace('medley','').replace('vocal','').replace('previously unreleased','').replace('remastering','').replace('remastered','').replace('various artists','').replace('vinyl','').replace('from','').replace('theme','').replace('motion picture soundtrack','').replace('soundtrack','').replace('full length','').replace('original','').replace('version','').replace('feat.','').replace('comp.','').replace('vocal','').replace('instrumental','').replace('&','and').replace('excerpt','').replace('single','').replace('album','').replace('anonymous','').replace('unknown','').replace('traditional','').replace('  ',' ')
        return(text.strip())

    def camp(self,query,ort,oit):
        tl = []
        try:
            url = f"https://bandcamp.com/search?q={query}&item_type=t"
            soup = bs(self.req(url).content, "html.parser")
            tracks = soup.select('.data-search')
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
        except:
            print(f'. . . . .n.a.{ort[:5]}/{oit[:5]}',end='\r')
        return(tl)

    def search(self,show):

        shelf = ipa._j2d(f'./json/{show}')
        flags = ipa._j2d(f'./bandcamp/{show}')
        spotify = ipa._retriv(show,'flags')
        
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

                        tl = self.camp(quer1,ort,oit)
                        if not tl:
                            if spotify[episode][trdx]['ratio'] >= 3:
                                print('. . . .t.a.s.',end='\r')
                                ort = spotify[episode][trdx]["artist"] # original artist
                                oit = spotify[episode][trdx]["title"] # original title
                                track = f'{ort} {oit}'
                                quer2 = urllib.parse.quote(track)
                                tl = self.camp(quer2,ort,oit)
                            else:
                                print('. . . .t.a.o.',end='\r')
                                quer2 = urllib.parse.quote(self.refine(unidecode(track)))
                                tl = self.camp(quer2,ort,oit)

                        if tl:
                            flags[episode][trdx] = tl[0]
                        else:
                            flags[episode][trdx] = dict()

                        ipa._d2j(f'./bandcamp/{show}',flags)

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

    def run(self,shows=[]):

        if shows:
            partition = shows

        else:
        
            galf = ipa._j2d('./extra/galf')
            sublist = [x for x in ipa.showlist if x in galf]

            ipa.wait('flg',True)
            with open('./extra/bait.pickle', 'rb') as handle:
                pick = pickle.load(handle)
            pick += 1
            lim = 20
            if pick >= lim:
                pick = 0
            with open('./extra/bait.pickle', 'wb') as handle:
                pickle.dump(pick, handle, protocol=pickle.HIGHEST_PROTOCOL)
            partition = sublist[pick::lim]
            print(f'\ncurrent Pickle : {pick}\n')
            ipa.wait('flg',False)

        par = {str(m) : partition[m] for m in range(len(partition))}
        print(par)

        for show in partition:
            if ipa.prerun(show,'json','bandcamp'):
                print(f'{show[:8]}. . . . . .S',end='\r')
                spo.run([show]) # double check
                self.search(show)
            else:
                print(f'skip : {show}')
            ipa.showhtml(show)
        ipa.home()