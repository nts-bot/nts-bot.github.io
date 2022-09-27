# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import script
nts = script.nts()

# nts.runscript(nts.showlist,fast=True)
nts.runscript(['nts-picks'],False)