'''
# from selenium import webdriver
# from selenium.webdriver.support.ui import WebDriverWait
# import pandas as pd 
# import re

# chrome_options = Options()
# chrome_options.add+argument

# options = webdriver.ChromeOptions()
# options.add_experimental_option('excludeSwitches', ['enable-logging'])
# driver = webdriver.Chrome(executable_path='C:\chrome\chromedriver_win32\chromedriver.exe', options=options)
# url = 'https://www.youtube.com/watch?v=D4pxIxGdR_M&t=2s'
# driver.get(url)
# driver.implicitly_wait(10)

# SCROLL_PAUSE_TIME = 3
'''
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

# url = 'https://www.youtube.com/watch?v=fzRnKbq_WSo'
url = 'https://www.youtube.com/watch?v=fGtoKUWjybI&'
driver.get(url)
#driver.implicitly_wait(20)
#time.sleep(5)

SCROLL_PAUSE_TIME = 3
# driver.get("https://youtube.com")

# Get scroll height
last_height = driver.execute_script(
    "return document.documentElement.scrollHeight")

while True:
  # Scroll down to bottom
  driver.execute_script(
      "window.scrollTo(0, document.documentElement.scrollHeight);")

  # Wait to load page
  time.sleep(SCROLL_PAUSE_TIME)

  # Calculate new scroll height and compare with last scroll height
  new_height = driver.execute_script(
      "return document.documentElement.scrollHeight")
  if new_height == last_height:
    break
  last_height = new_height

html_source = driver.page_source

#soup = BeautifulSoup(html_source, 'lxml')

from selenium.webdriver.common.by import By

# ids = driver.find_elements_by_xpath('//*[@id="author-text"]/span');
# comments = driver.find_elements_by_xpath('//*[@id="content-text"]');
# likes = driver.find_elements_by_xpath('//*[@id="vote-count-middle"]')

ids = driver.find_elements(By.XPATH, '//*[@id="author-text"]/span')
comments = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
likes = driver.find_elements(By.XPATH, '//*[@id="vote-count-middle"]')

# ids = soup.select('div#header-author > a > span')

# comments = soup.select('div#content > yt-formatted-string#content-text')

# likes = soup.select('ytd-comment-action-buttons-renderer#action-buttos > div#tollbar > span#vote-count-middle')

print('ID :', len(ids), 'Comments : ', len(comments), 'Likes : ', len(likes))

open('output_test.txt', 'w').close()
file1 = open("output_test.txt", "a")
for id,comment,like in zip(ids,comments,likes):
  # print(id.text)
  # print(comment.text)
  # print(like.text)
  #file1.write(id.text)
  file1.write("Comment: " + "\"" + comment.text + "\"" + "   ")
  file1.write("Number of Likes for Comment: " + like.text)
  file1.write("\n")

print("DONE 4Real")
# print(ids.text)
# print(comments.text)
# print(likes.text)

