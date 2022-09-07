# Inbuilt Libraries
import os, json, time, requests, re, pickle
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
        
    def _d2j(self,path,allot):
        try:
            if isinstance(allot,dict):
                with open(f"{path}.json", 'w', encoding='utf-8') as f:
                    json.dump(allot, f, sort_keys=True, ensure_ascii=False, indent=4)
            else:
                raise ValueError(f'You are trying to dump {type(allot)} instead dict()')
        except PermissionError as error:
            print(f'Permission Error : {error}')
            time.sleep(1.0)
            self._d2j(path,allot)
        except OSError as error:
            raise OSError(f'CWD : {os.getcwd()} ; PATH : {path} ; ERROR : {error}')

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

    ''' LATEST '''

    def latest(self,url="https://www.nts.live/latest"): 
        soup = self.browse(url)
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

    def N2J(self,show,amount=1):
        soup = self.browse(f"https://www.nts.live/shows/{show}")
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

        self._d2j(f'./json/{show}',shelf)

    def tracklist(self,show):
        
        print(show, end='\r')
        shelf = self._j2d(f'./json/{show}')

        for i in shelf.keys():
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

    def html(self):
        # HTML HEAD
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
            <h1><a href="https://github.com/nts-bot/nts-bot.github.io">NTS-bot</a></h1>
        """

        # [1] index
        
        doc += '<br><details><summary><h2>index</h2></summary><blockquote class="index">'

        for i in self.showlist[:-1]:
            doc += f'<a href="#{i}">{i}</a>||'
        doc += f'<a href="#{self.showlist[-1]}">{self.showlist[-1]}</a></blockquote></details><br>'

        # [2] For each show write : SHOW : [nts] | [spotify] | [bandcamp] : [json1] | [json2] | [json3]

        pid = self._j2d('pid')
        bid = self._j2d('bid')
        title = self._j2d('./extra/titles')

        try:
            ex = title[i]
        except KeyError:
            title, desk = self.bio(i)

        doc += "<ul>"

        for i in self.showlist:

            print(i,end='\r')

            item = f"""<li><a id="{i}" class="title" href="https://www.nts.live/shows/{i}">{title[i]}</a>"""
            son = f'<a href="./json/{i}.json">nts-tracklist</a>'

            if i in pid:
                surl = f'<a href="https://open.spotify.com/playlist/{pid[i]}">spotify-playlist</a>'
                sson = f'<a href="./spotify/{i}.json">spotify-tracklist</a>'
            else:
                surl=f'<a class="none">(wip)</a>'
                sson=f'<a class="none">(wip)</a>'
                
            if i in bid:
                if bid[i]:
                    burl=f'<a href="https://bndcmpr.co/{bid[i]}">bandcamp-playlist</a>'
                    bson=f'<a href="./bandcamp/{i}.json">bandcamp-tracklist</a>'
                else:
                    burl=f'<a class="none">(empty)</a>'
                    bson=f'<a href="./bandcamp/{i}.json">bandcamp-tracklist</a>'
            else:
                burl=f'<a class="none">(wip)</a>'
                bson=f'<a class="none">(wip)</a>'

            doc += f"""{item}
            <span class="data">{son}</span>
            <span class="playlist">{surl}</span>
            <br>
            <span class="data">{sson}</span>
            <span class="playlist">{burl}</span>
            <br>
            <span class="data">{bson}</span>"""

        doc += '''</ul><br><br><br><br></body></html>'''

        ''' [03] SOUPIFY AND SAVE '''

        soup = bs(doc, "lxml")
        pretty = soup.prettify() 
        with open(f"index.html", 'w', encoding='utf8') as f:
            f.write(pretty)
