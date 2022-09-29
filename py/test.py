# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import script
nts = script.nts()

show = input('Input Show\n')

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

# nts.runscript(shows) #[show]

nts.runscript([show])