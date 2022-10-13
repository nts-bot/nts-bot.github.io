# Environment Variables
from dotenv import load_dotenv
load_dotenv()
import warnings
warnings.filterwarnings("ignore")
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import script
nts = script.nts()

# show = input('Input Show\n')
# nts.runscript([show])

# import datetime
# shows = []
# tday = datetime.date.today()
# day = [tday]
# for i in range(1,8):
#     day += [tday - datetime.timedelta(i)]
# for i in nts.showlist:
#     sday = datetime.datetime.fromtimestamp(os.path.getmtime(f"./tracklist/{i}.json")).date()
#     if sday in day:
#         shows += [i]

shows = ['shanticeleste','well-street-records','thea-hd','uline-catalog','sun-cut','tom-boogizm','panorama-yerevan','physical-therapy','red-laser-records','relax-w-reni','stephen-omalley','test-pressing','okonkole-y-trompa','radio-ghibli','british-library-sound-archive','guitar-world','timeisaway','space-afrika','early-bird-show-jack-rollo','early-bird-show-maria-somerville','early-bird-show-spirit-blue','malibu','claire-rousay','the-trilogy-tapes','tommasi','great-southern-lands','suki-sou','claire-milbrath','athens-of-the-north','perfume-advert','mafalda','john-carroll-kirby','jamie-xx','sun-cut','macca','yaeji','carla-dal-forno','soup-to-nuts-lupini','the-breakfast-show-flo','donna-leake','jen-monroe','kaitlyn-aurelia-smith','floating-points','music-4-lovers','fifth-world','rhythmconnection']
# shows = list(nts._j2d('./yid').keys())[::-1]
nts.runscript(shows)

# shows = nts.showlist
# j = 0
# for i in range(0, len(shows), 5):
#     nts.runscript(shows[j:i]) #[show]
#     j = int(i)

# for show in shows[::-1]:
# for show in nts.showlist:
#     nts.runner(show,f"./spotify/{show}",3)

#