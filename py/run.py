# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import script
nts = script.nts()

am = 100 #15 # 50 ~ a week of shows

soup = nts.browse("https://www.nts.live/latest",amount=am)
episodes = soup.select('a.nts-grid-v2-item__header')
shelf = dict()
for i in episodes:
    href = i['href']
    show = href.split('/')[2]
    epis = href.split('/')[-1]
    shelf[show] = [epis]
nts.runscript(list(shelf.keys())[::-1])
