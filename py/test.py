# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import script
nts = script.nts()

# nts.runscript(['5-gate-temple'])
show = 'blazer-sound-system'
nts.searchloop(show,['tracklist','bandcamp','spotify'],'bandcamp')