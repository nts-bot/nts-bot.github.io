
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
bc.run()

#
