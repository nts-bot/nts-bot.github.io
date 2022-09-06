
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
print('SEARCHING')
bc.run_search()
# print('PLAYLISTING')
# bc.run_playlist()
# bc.html()

#
