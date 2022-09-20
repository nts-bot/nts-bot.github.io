# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Directory
import os, git

try:
    repo = git.Repo(os.getenv("directory"))
    repo.git.add('.') #update=True
    repo.index.commit("auto-gitpush")
    origin = repo.remote(name='origin')
    origin.push()
except Exception as error:
    print(f'Error : {error}')  