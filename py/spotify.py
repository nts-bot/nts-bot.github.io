# BASIC
import os,pickle,time
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

# PRE-INIT
from dotenv import load_dotenv
load_dotenv()
# LOAD LOCAL PYTHON CLASS FILE
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import api
ipa = api.api()

class nts:

    def __init__(self):
        ''' LOAD DIRECTORY '''
        dr = os.getenv("directory")
        os.chdir(f"{dr}")

    #############################################

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
        ipa.wait('connect',True)
        try:
            with open('./extra/spotipywebapi.pickle', 'rb') as handle:
                pick = pickle.load(handle)
            print(index[pick])
            self.subconnect(index,pick)
            ipa.wait('connect',False)
        except Exception:
            self.conexcp()

    def conexcp(self,):
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
            ipa.wait('connect',False)

        except Exception:
            self.conexcp()

    #############################################

    def _unknown(self,i): # i is show
        ''' REMOVE UNKNOWNS '''
        a = ipa._retriv(i,'flags')
        for j in a:
            for k in a[j]:
                if 'Unknown Artist' in a[j][k]['artist']:
                    a[j][k]["ratio"] = -1
                    a[j][k]["uri"] = ''
                if 'Unknown' == a[j][k]['artist']:
                    a[j][k]["ratio"] = -1
                    a[j][k]["uri"] = ''
        ipa._shelve(i,'flags',a)

    ##############################################

    def pid(self,show):
        ''' GET/CREATE SHOW PLAYLIST ID '''
        pid = ipa._j2d('pid')
        try:
            shelf = pid[show]
            return(shelf)
        except KeyError:
            ipa.images(show)
            #
            tim = ipa._j2d('./extra/srch')
            tim[show] = 1
            ipa._d2j('./extra/srch',tim)
            #
            ref = self.sp.user_playlist_create(self.user,f'{show}-nts',public=True,description=f"(https://www.nts.live/shows/{show})")
            pid[show] = ref['id']
            ipa._d2j('pid',pid)
            return(ref['id'])

    def search(self,show):
        ''' SEARCH EPISODES VIA SPOTIFY API '''
        shelf = ipa._j2d(f'./json/{show}')
        flags = ipa._retriv(show,'search')

        c = 0

        for episode in shelf:
            coal = False

            c += 1
            print(f'. . . . . . . . . . . . . . . . .{c}:{len(list(shelf.keys()))}.',end='\r')

            try:
                flags[episode]
            except (KeyError,TypeError) as error:
                try:
                    flags[episode] = dict()
                except TypeError as error:
                    return False
            
            if list(set(shelf[episode].keys())-set(flags[episode].keys())):
                print(f'{episode[:10]}:{episode[-10:]}',end='\r')
                for trdx in shelf[episode]:
                    if (trdx not in flags[episode]): 
                        coal = True

                        q0= f'artist:{shelf[episode][trdx]["artist"]} track:{shelf[episode][trdx]["title"]}'
                        q1 = f'{shelf[episode][trdx]["artist"]} : {shelf[episode][trdx]["title"]}'
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
                        flags[episode][trdx] = {'s0':S0,'s1':S1}

            if coal:
                ipa._shelve(show,'search',flags)

    def rate(self,show):
        ''' COMPARE SEARCH RESULTS AGAINST ORIGINAL QUERY : ASSIGN RATING TO RESULT '''
        shelf = ipa._j2d(f'./json/{show}')
        search = ipa._retriv(show,'search')
        flags = ipa._retriv(show,'flags')

        c = 0
        
        for episode in shelf:
            coal = False
            cc = 0
            c += 1
            print(f'. . . . . . . . . . . . . . . . .{c}:{len(list(shelf.keys()))}.',end='\r')
            
            try:
                flags[episode]
            except (KeyError,TypeError) as error:
                try:
                    flags[episode] = dict()
                except TypeError as error:
                    return False
            
            if list(set(shelf[episode].keys())-set(flags[episode].keys())):
                print(f'{episode[:10]}:{episode[-10:]}',end='\r')
                for trdx in shelf[episode]:
                    cc += 1
                    if (trdx not in flags[episode]):
                        print(f'. . . . . . . . . . . . . .{cc}:{len(list(shelf[episode].keys()))}.',end='\r')
                        coal = True 

                        qa = shelf[episode][trdx]["artist"]
                        qt = shelf[episode][trdx]["title"]
                        s0 = search[episode][trdx]['s0']
                        s1 = search[episode][trdx]['s1']

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
                                flags[episode][trdx] = {'artist':eval(f'a{dx}'),'title':eval(f't{dx}'),'ratio':lag,'trackid':eval(f'u{dx}')}
                            else:
                                flags[episode][trdx] = {'artist':eval(f'a{dx}'),'title':eval(f't{dx}'),'ratio':-1,'trackid':''}
                        else:
                            flags[episode][trdx] = {'artist':'','title':'','ratio':-1,'trackid':''}
            if coal:
                ipa._shelve(show,'flags',flags)

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
        return(SequenceMatcher(None, a, b).ratio())

    def kill(self,text):
        ''' ELIMINATE DUPLICATES & UNNECESSARY CHARACTERS WITHIN STRING '''
        cv = text.replace('・',' ').replace('+',' ').replace(']',' ').replace('[',' ').replace(')',' ').replace('(',' ').replace('\'',' ').replace('\"',' ').replace('-',' ').replace('!',' ').replace('/',' ').replace(';',' ').replace(':',' ').replace('.',' ').replace(',',' ').split(' ')
        return(" ".join(dict.fromkeys(cv)))

    def refine(self,text):
        ''' ELIMINATE UNNECCESARY WORDS WITHIN STRING '''
        text = self.kill(text)
        for i in list(range(1990,2022)):
            text = text.replace(str(i),'')
        return text.replace('selections','').replace('with ','').replace('medley','').replace('vocal','').replace('previously unreleased','').replace('remastering','').replace('remastered','').replace('various artists','').replace('vinyl','').replace('from','').replace('theme','').replace('motion picture soundtrack','').replace('soundtrack','').replace('full length','').replace('original','').replace(' mix ',' mix mix mix ').replace('remix','remix remix remix').replace('edit','edit edit edit').replace('live','live live live').replace('cover','cover cover cover').replace('acoustic','acoustic acoustic').replace('demo','demo demo demo').replace('version','').replace('feat.','').replace('comp.','').replace('vocal','').replace('instrumental','').replace('&','and').replace('zero','0').replace('one','1').replace('two','2').replace('three','3').replace('unsure','4').replace('almost','5').replace('six','6').replace('seven','7').replace('eight','8').replace('nine','9').replace('excerpt','').replace('single','').replace('album','').replace('anonymous','').replace('unknown','').replace('traditional','')

    def comp(self,a,b,c,d): #OA, #OT, #SA, #ST
        ''' COMPARISON FUNCTION '''
        l1, t1 = self.trnslate(a) # O AUTHOR
        l2, t2 = self.trnslate(b) # O TITLE
        l3, t3 = self.trnslate(c) # S AUTHOR
        l4, t4 = self.trnslate(d) # S TITLE

        k1, k2 = self.refine(l1.lower()), self.refine(l2.lower())
        k3, k4 = self.refine(l3.lower()), self.refine(l4.lower())

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

    ##############################################################

    def scene(self,sequence):
        ''' GET UNIQUE ITEMS IN LIST & IN ORDER '''
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def _add(self,show,threshold=[3,10],remove=False,reset=False,image=True):
        ''' APPEND/CREATE/REMOVE FROM SPOTIFY PLAYLIST '''
        self._unknown(show)
        pid = self.pid(show)
        flags = ipa._retriv(show,'flags')

        tid = []
        pup = []
        mis = 0
        almost = 0
        unsure = 0

        for episodes in flags:
            for track in flags[episodes]:
                if threshold[0] <= flags[episodes][track]['ratio'] <= threshold[1]:
                    tid += [flags[episodes][track]['trackid']]
                pup += [flags[episodes][track]['trackid']]
                if not flags[episodes][track]['trackid']:
                    mis += 1
                if threshold[0]  <= flags[episodes][track]['ratio'] == 4:
                    almost += 1
                if threshold[0]  <= flags[episodes][track]['ratio'] <= 3:
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
            ipa.flag(show,False)
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
                self.sp.user_playlist_add_tracks(self.user, pid, i, position=0)
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

        title, desk = ipa.bio(show)
        desk = desk.replace('\n',' ').replace('\\','').replace('\"','').replace('\'','').strip()
        syn = f"[Archive of (www.nts.live/shows/{show}) : {almost}{unsure} {mis+len(set(pup))-len(set(tid))} missing. Tracks are grouped by episode]"
        
        z = self.sp.user_playlist_change_details(self.user,pid,name=f"{title} - NTS",description=f"{desk} {syn}")

        if image:
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
                self.sp.playlist_upload_cover_image(pid, b64_string)
            except Exception as error:
                print(f'image failure for show : {show} : Error : {error}')
        
    ##############################################################

    def follow(self,usr=1,kind='cre'):
        ''' SECONDARY SPOTIFY USERS WHO MAINTAIN ALPHABETICALLY ORGANIZED PLAYLISTS BELOW SPOTIFY (VISIBLE) PUBLIC PLAYLIST LIMIT (200) '''
        creds = ipa._j2d(f'{kind}dentials')
        user = creds[str(usr)]['user']
        cid = creds[str(usr)]['cid']
        secret = creds[str(usr)]['secret']
        callback = 'http://localhost:8888/callback'
        spot = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=cid,client_secret=secret,redirect_uri=f"{callback}",scope='playlist-modify-public user-follow-modify',username=user), requests_timeout=5, retries=5)
        print('Testing . . .')
        test = spot.user(user)
        print('. . . . . . . . Successful',end='\r')
        
        if kind == 'cre':
            extent = ipa.showlist[(200 * (usr - 1)):(200 * (usr))]
        elif kind == 'pre':
            extent = ipa.showlist

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

    ##############################################################

    def run(self,shows=[]):
        ''' FUNCTION WHICH RUNS EVERYTHING ABOVE (BUT meet(); WHICH UPDATES FOR NEW SHOWS)  '''
        import warnings
        warnings.filterwarnings("ignore")

        for l in ['flg','glf','wait','connect']:
            with open(f'./extra/{l}.pickle', 'wb') as handle:
                pickle.dump(0, handle, protocol=pickle.HIGHEST_PROTOCOL)

        try:
            galf = ipa._j2d('./extra/galf')

            if shows:
                yek = shows 

            else:

                flag = ipa._j2d('./extra/flag')

                if not flag:
                    yek = [x for x in ipa.showlist if x not in galf]#[::20]
                else:
                    yek = list(flag.keys())[::-1]

                if len (yek) > 40:
                    ipa.wait('flg',True)
                    with open('./extra/flag.pickle', 'rb') as handle:
                        pick = pickle.load(handle)
                    pick += 1
                    lim = 10
                    if pick >= lim:
                        pick = 0
                    with open('./extra/flag.pickle', 'wb') as handle:
                        pickle.dump(pick, handle, protocol=pickle.HIGHEST_PROTOCOL)
                    yek = yek[pick::lim]
                    print(f'\ncurrent Pickle : {pick}\n')
                    ipa.wait('flg',False)
                else:
                    ipa.wait('flg',True)
                    pass
                
            par = {str(m) : yek[m] for m in range(len(yek))}
            pprint(par)

            time.sleep(2.0)

            self.connect()

            for k in par:

                i = par[k]

                print(f'.{(i+". . . . . . . . . .")[:20]}. . .{k}/{len(yek)}.',end='\r')
                print('.')

                if i not in galf:
                    res, ims = True, True
                    ipa.N2J(i,100) #100
                    ipa.tracklist(i)
                else:
                    res, ims = False, False

                print('. . . . . . . . . . .S.',end='\r')
                self.search(i)
                time.sleep(0.5)
                
                if i not in galf:

                    print('. . . . . . . . . . .kill.',end='\r')
                    ppp = ipa._j2d(f'./spotify/{i}')
                    del ppp['flags']
                    time.sleep(0.5)
                    ipa._d2j(f'./spotify/{i}',ppp)
                    
                print('. . . . . . . . . . .R.',end='\r')
                self.rate(i)
                time.sleep(0.5)

                print('. . . . . . . . . . .A.',end='\r')
                self._add(show=i,reset=res,image=ims)
                ipa.flag(i,False)
                print('.')

                if i not in galf:
                    ipa.flag(i,True,'galf','glf')
                     
        except Exception as error:
            for l in ['flg','glf','wait','connect']:
                with open(f'./extra/{l}.pickle', 'wb') as handle:
                    pickle.dump(0, handle, protocol=pickle.HIGHEST_PROTOCOL)
            raise RuntimeError(error)
    
# END