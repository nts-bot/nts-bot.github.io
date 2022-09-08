
# Inbuilt Libraries
import os, json, time, requests, re, pickle, urllib
# Html Parser
from bs4 import BeautifulSoup as bs
# Browser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# Environment Variables
from dotenv import load_dotenv
load_dotenv()

class nts:

    def __init__(self):
        dr = os.getenv("directory")
        os.chdir(f"{dr}")
        self.showlist = [i.split('.')[0] for i in os.listdir('./json/')]

    # DATA COLLECTION


    # WEBSCRAPING


    # SPOTIFY API


    # HTML