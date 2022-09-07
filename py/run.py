
# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os
dr = os.getenv("directory")
os.chdir(f"{dr}/py")
import bandcamp
bc = bandcamp.nts()
import api, time
ipa = api.api()
os.chdir(f"{dr}/py")
import spotify
stn = spotify.nts()

# UPDATE NEW FILES

print("\n STEP 1")

ipa.latest()
ipa.update()
time.sleep(1.0)

son = ipa._j2d('./extra/update')
for i in list(son.keys())[::-1]:
    print(i,end='\r')
    ipa.flag(i)
    del son[i]
    ipa._d2j('./extra/update',son)

print("\n STEP 2")

dos = ipa._j2d('./extra/flag')
stn.run(dos)
bc.run(dos)