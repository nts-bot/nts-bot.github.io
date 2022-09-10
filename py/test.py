# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import script
nts = script.nts()

shows = ['the-breakfast-show-flo','early-bird-show-maria-somerville']
nts.runscript(shows)