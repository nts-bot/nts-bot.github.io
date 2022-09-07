
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
sub = [i for i in showlist if i not in os.listdir('./discogs/')]
for i in sub:
    bc.dearch(i)
    
#
