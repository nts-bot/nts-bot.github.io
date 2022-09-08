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
# Environment Variables
from dotenv import load_dotenv
load_dotenv()

class api:

    def __init__(self):
        dr = os.getenv("directory")
        os.chdir(f"{dr}")
        self.showlist = [i.split('.')[0] for i in os.listdir('./json/')]

    def _shelve(self,shelf,yek,allot,loc='spotify'):
        wohs = self._j2d(f"./{loc}/{shelf}")
        wohs[yek] = allot
        self._d2j(f"./{loc}/{shelf}",wohs)

    def _retriv(self,shelf,yek,loc='spotify'):
        try:
            wohs = self._j2d(f"./{loc}/{shelf}")
            return(wohs[yek])
        except KeyError:
            print('                         .KE.',end='\r')
            self._shelve(shelf,yek,dict())
            time.sleep(0.5)
            return(self._retriv(shelf,yek))

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
        
    def _d2j(self,path,allot,c=0):
        try:
            if isinstance(allot,dict):
                with open(f"{path}.json", 'w', encoding='utf-8') as f:
                    json.dump(allot, f, sort_keys=True, ensure_ascii=False, indent=4)
            else:
                raise ValueError(f'You are trying to dump {type(allot)} instead dict()')
        except:
            c += 1
            if c > 10:
                raise RuntimeError('_d2j Runtime Error')
            print(f'Error When Storing JSON')
            time.sleep(1.0)
            self._d2j(path,allot,c)

    #############################################

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

    ''' SHOWS '''

    def shows(self,url="https://www.nts.live/shows"): 
        soup = self.browse(url)
        shows = soup.select('a.grid-item')
        showlist = [i.replace('.json','') for i in os.listdir('./json/') if '.json' in i[-5:]]
        print(showlist)
        for i in shows:
            href = i['href']
            show = href.split('/')[2]
            print(show,end='\r')
            if show not in showlist:
                print(f'. . . . . . . .CREATING.',end='\r')
                self._d2j(f'./json/{show}',dict())
                self.flag(show)
            else:
                print(f'. . . . . . . .EXISTS.',end='\r')

            self.getmeta(show,soup)

    ''' LATEST '''

    def latest(self,url="https://www.nts.live/latest"): 
        soup = self.browse(url,amount=2)
        episodes = soup.select('a.nts-grid-v2-item__header')
        shelf = self._j2d('./extra/update')
        for i in episodes:
            href = i['href']
            show = href.split('/')[2]
            epis = href.split('/')[-1]
            print(f'{show} : {epis}',end='\r')
            shelf[show] = []
            shelf[show] += [epis]
            shelf[show] = list(set(shelf[show]))

        self.getmeta(show,soup)

        self._d2j('./extra/update',shelf)

    def update(self):
        son = self._j2d('./extra/update')
        for i in son.keys():
            ex1 = self._retriv(i,'search')
            ex2 = self._retriv(i,'flags')
            shelf = self._j2d(f'./json/{i}') # episodes retrieve
            for j in son[i]:
                if j not in shelf.keys():
                    print(j,end='\r')
                    shelf[j] = dict()
            self._d2j(f'./json/{i}',shelf) # episodes store
            print('. . . . . . . . . . .Getting Tracklist.',end='\r')
            self.tracklist(i)
            son[i] = []
        self._d2j('./extra/update',son)
        
    ''' NTS 2 JSON '''

    def N2J(self,show,amount=10):
        soup = self.browse(f"https://www.nts.live/shows/{show}",amount=amount)
        grid = soup.select(".nts-grid-v2")
        shelf = self._j2d(f'./json/{show}')

        for i in grid[0]:
            a = i.select('a')
            if a:
                href = a[0]['href']
                episode = href.split('/episodes/')[1]
                if episode not in shelf.keys():
                    print(f'. . . . . . .{episode[-10:]}.', end='\r')
                    shelf[episode] = dict()
                else:
                    print(f'. . . . . . .{episode[-5:]}. skip', end='\r')
            else:
                print('href failed')

        self.getmeta(show,soup)

        self._d2j(f'./json/{show}',shelf)

    def tracklist(self,show):
        
        print(show, end='\r')
        shelf = self._j2d(f'./json/{show}')
        try:
            meta = self._j2d(f'./extra/meta')[show]
        except:
            meta = shelf

        for i in meta:
            print('.',end='\r')
            if shelf[i]:
                pass
            elif isinstance(shelf[i],dict) and not shelf[i]:
                print(i[:10], end='\r')
                url = f"https://www.nts.live/shows/{show}/episodes/{i}"
                soup = bs(requests.get(url).content, "html.parser")
                tracks = soup.select('.track')
                for j in range(len(tracks)):
                    print(f'{i[:10]}:{j:02}', end='\r')
                    try:
                        shelf[i][f"{j:02}"] = {
                            "artist" : f"{tracks[j].select('.track__artist')[0].get_text()}",
                            "title" : f"{tracks[j].select('.track__title')[0].get_text()}"
                        }
                    except IndexError:
                        print('Index Error')
                        try:
                            shelf[i][f"{j:02}"] = {
                            "artist" : f"{tracks[j].select('.track__artist')[0].get_text()}",
                            "title" : ""
                        }
                        except IndexError:
                            shelf[i][f"{j:02}"] = {
                            "artist" : f"",
                            "title" : f"{tracks[j].select('.track__title')[0].get_text()}"
                        }
            else:
                shelf[i] = ''

        self._d2j(f'./json/{show}',shelf)

    ''' EXTRA '''

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

    def getmeta(self,show,soup):
        grid = soup.select('.nts-grid-v2-item__content')
        meta = self._j2d(f'./extra/meta')
        for i in grid:
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
        self._d2j(f'./extra/meta',meta)

    def meta(self,shw=''):
        meta = self._j2d(f'./extra/meta')
        if shw:
            sub = [shw]
            ret = True
        else:
            sub = self.showlist
            ret = False
        for show in sub:
            shelf = self._j2d(f'./json/{show}')
            try:
                store = meta[show]
            except KeyError:
                meta[show] = dict()
                store = meta[show]
            ok = [False]
            for i in shelf: # episodes
                if i not in store:
                    ok += [True]
                else:
                    pass

            if any(ok):
                shelf = self._j2d(f'./json/{show}')
                scroll = round(len(shelf)/12)
                print(scroll)
                url = f"https://www.nts.live/shows/{show}"
                if scroll <= 1:
                    soup = bs(self.req(url).content, "html.parser")
                else:
                    soup = self.browse(url,amount=scroll)
                self.getmeta(show,soup)
                if ret:
                    return(True)
            else:
                print('skip')
                if ret:
                    return(False)

    def images(self,path):
        imlist = [i.split('.')[0] for i in os.listdir('./jpeg/')]
        if path not in imlist:
            url = f"https://www.nts.live/shows/{path}"
            soup = bs(requests.get(url).content, "html.parser")
            back = soup.select('.background-image')
            if back:
                img = re.findall('\((.*?)\)',back[0].get('style'))[0]
                img_data = requests.get(img).content
                extension = img.split('.')[-1]
                with open(f'./jpeg/{path}.{extension}', 'wb') as handler:
                    handler.write(img_data)
            else:
                print('. . . . . . . . .Image not found.', end='\r')

    def bio(self,show):
        print(f'. . . .bio:{show[:5]}',end='\r')
        titlelist = self._j2d('./extra/titles')
        desklist = self._j2d('./extra/descriptions')
        try:
            title = titlelist[show]
            desk = desklist[show]
        except KeyError:
            print('KE',end='\r')
            url = f"https://www.nts.live/shows/{show}"
            soup = bs(requests.get(url).content, "html.parser")
            back = soup.select('.bio')
            if back:
                title = back[0].select('.bio__title')[0].select('h1')[0].text
                desk = back[0].select('.description')[0].text
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
            print('.saving-bio.',end='\r')
            titlelist[show] = title
            desklist[show] = desk
            self._d2j('./extra/titles',titlelist)
            self._d2j('./extra/descriptions',desklist)

        return(title, desk)

    ''' FACILITATE AUTOMATION '''

    def flag(self,show,flag=True,title='flag',pick='wait'):
        self.wait(pick,True)
        tim = self._j2d(f'./extra/{title}')
        try:
            tim[show]
        except KeyError:
            tim[show] = dict()
        if flag:
            tim[show] = 1
        else:
            del tim[show]
        self._d2j(f'./extra/{title}',tim)
        self.wait(pick,False)

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

    def prerun(self,show,d1,d2): # useful for bandcamp script since we skip opening selenium

        js1 = self._j2d(f'./{d1}/{show}')
        js2 = self._j2d(f'./{d2}/{show}')
        ok = [False]

        for i in js1: # episodes
            if i not in js2:
                ok += [True]
            else:
                for j in js1[i]: # tracks
                    if j not in js2[i]:
                        ok += [True]
                    else:
                        ok += [False]

        return(any(ok))

    #

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
            try:
                tit = title[shw]
                if not tit:
                    tit = shw
            except KeyError:
                tit, des = self.bio(shw)

            V = shw[0].lower()

            # print(shw, V)

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

    #

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

        episodes = self._j2d(f'./json/{show}')
        spotify = self._j2d(f'./spotify/{show}')['flags']
        bandcamp = self._j2d(f'./bandcamp/{show}')
        discogs = self._j2d(f'./discogs/{show}')

        meta = self._j2d(f'./extra/meta')[show]
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
                    dc = discogs[i][j]['url']
                    dis = f"""<a class="goto" href="{dc}">🗃️</a>  """
                except:
                    dis = ''
                
                try:
                    if spotify[i][j]['ratio'] >= 3:
                        sp = f"""https://open.spotify.com/track/{spotify[i][j]['trackid']}"""
                        spo = f"""<a class="goto" href="{sp}">🟢</a>  """
                    else:
                        spo = ''
                except:
                    spo = ''

                if any([bnd,dis,spo]):
                    colon = ':'
                else:
                    colon = ''

                doc += f"""<li>{tart} - {ttit}   {colon}   <span class="data">{spo}{bnd}{dis}</span></li>""" #{tub}

            doc += '</ol></details>'

        doc += '''<br><br><br></body></html>'''

        ''' [03] SOUPIFY AND SAVE '''

        soup = bs(doc, "lxml")
        pretty = soup.prettify() 
        with open(f"./html/{show}.html", 'w', encoding='utf8') as f:
            f.write(pretty)


