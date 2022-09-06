
# START

import os
# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import spotify
stn = spotify.nts()

stn.run() #['jen-monroe'])

# END