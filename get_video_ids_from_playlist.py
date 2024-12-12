# Get all video ids from a playlist given the playlist link
# HUGE THANKS: https://gist.github.com/milankragujevic/cf0e503407104b1e444efa18f4108ce1


import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import sys

import colorama
# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Initialize the driver
driver = webdriver.Chrome(options=chrome_options)

url = 'https://www.youtube.com/playlist?list=PLVbP054jv0KoZTJ1dUe3igU7K-wUcQsCI'
driver.get(url)
# Run the JavaScript code
js_code = """
    var els = document.getElementsByClassName('yt-simple-endpoint style-scope ytd-playlist-video-renderer');
    var show="";
    for(i = 0;i<els.length;i++){
        var el = els[i];
        show += (el.href.split('?v=')[1].split('&list')[0] + "\\n");
    }
    return show;
"""
time.sleep(6)
driver.execute_script(
    "window.scrollTo(0, document.documentElement.scrollHeight);")

# Wait to load page
time.sleep(6)
# Execute the JavaScript code and retrieve the result
video_ids = driver.execute_script(js_code)

# Print the video IDs
print(video_ids)
with open("plvids.txt", "w") as file:
    file.write(video_ids + "\n")
# Close the webdriver
driver.quit()
