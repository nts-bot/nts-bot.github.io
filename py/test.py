# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import script
nts = script.nts()

# shows = ['the-breakfast-show-flo','early-bird-show-maria-somerville','early-bird-show-spirit-blue','corticeps','shanticeleste','patrickforge','fifth-world','high-jazz','tilly','htrk','carla-dal-forno','the-sam-wilkes-radio-hour','soup-to-nuts-lupini','donna-leake','jen-monroe','kaitlyn-aurelia-smith','floating-points','music-4-lovers','the-breakfast-show-zakia']
# nts.runscript(shows)
n = 63 + 72 + 64 #cc
nts.runscript(nts.showlist[n:])