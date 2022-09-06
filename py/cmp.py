
# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")

# RUN BANDCAMP API

import bandcamp
bc = bandcamp.nts()

showlist = [i.split('.')[0] for i in os.listdir('./json/')]

for i in showlist:
    print('SEARCHING')
    bc.search(i)
    print('PLAYLISTING')
    bc.playlist(i)
    bc.html()

#
