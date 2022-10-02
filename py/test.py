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
# nts.runscript([show],True)

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

# shows = ['radio-ghibli','british-library-sound-archive','guitar-world','timeisaway','space-afrika','early-bird-show-jack-rollo','early-bird-show-maria-somerville','early-bird-show-spirit-blue','malibu','claire-rousay','the-trilogy-tapes','tommasi','great-southern-lands','suki-sou','claire-milbrath','athens-of-the-north','perfume-advert','mafalda','john-carroll-kirby','jamie-xx','sun-cut','macca','yaeji','carla-dal-forno','soup-to-nuts-lupini','the-breakfast-show-flo','donna-leake','jen-monroe','kaitlyn-aurelia-smith','floating-points','music-4-lovers','fifth-world','rhythmconnection']
# nts.runscript(shows)

for i in nts._j2d('./yid'):
    nts.runscript([i]) #[show] #shows

end = input('End of Test')