# This script opens colleges in browser

import webbrowser
import json
import time

data = []

def get_url():
    with open("Medical_colleges.json","r",encoding='utf-8') as f:
        return json.load(f)
    
data = get_url()

for i in data[0:30]:
    time.sleep(0.5)
    link = f"{i['url']}/cutoff"
    webbrowser.open(link)