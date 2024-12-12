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


# URL of the YouTube video
url = 'https://www.youtube.com/watch?v=HqcwSyD4H44&'
driver.get(url)

# Scroll pause time
SCROLL_PAUSE_TIME = 3

# Get scroll height
last_height = driver.execute_script(
    "return document.documentElement.scrollHeight")

reply_buttons = []

comments = driver.find_elements(By.XPATH, "//ytd-comment-thread-renderer")

## SCROLL ALL THE WAY DOWN
while True:
    # Scroll down to bottom
    driver.execute_script(
        "window.scrollTo(0, document.documentElement.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)
    # reply_button_xpath = "//ytd-button-renderer[@id='more-replies']/a/paper button[@id='button']"
    # r = driver.find_elements(By.XPATH, reply_button_xpath)
    # r[0].click()
    # Find all reply buttons
    # reply_buttons = driver.find_elements(
    #     By.XPATH,
    #     "//ytd-button-renderer[@id='more-replies']/a/paper-button[@id='button']")
    # Calculate new scroll height and compare with last scroll height

    # reply_buttons = driver.find_elements(By.XPATH, '//*[@id="more-replies"]')#'//*[@id="more-replies"]/yt-button-shape/button')
    # # # Click each reply button that hasn't been clicked yet
    # for button in reply_buttons:
    # #     # if button.is_enabled() and button.is_displayed():
    # #     # driver.execute_script("arguments[0].scrollIntoView(true);", button)
    #     driver.execute_script("arguments[0].click();", button)
    #     time.sleep(1)

    #     if button.is_enabled():
    #         button.click()
    new_height = driver.execute_script(
        "return document.documentElement.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Get HTML source
html_source = driver.page_source

comments_xpath = '//*[@id="content-text"]'
comments = driver.find_elements(By.XPATH, comments_xpath)

# ORIG COMMENTS ONLY
with open("comments.txt", "w") as file:
    for comment in comments:
        # file.write("Comment: " + comment.text + "\n")
        file.write(comment.text + "\n")
        # parent_element = comment.find_element(By.XPATH, "./ancestor::*[1]")
        # if "ytd-comment-thread-renderer" == parent_element.get_attribute("class"):
        #     file.write("Actual Comment: " + comment.text + "\n")
        # else:
        #     file.write("Sub-Reply: " + comment.text + "\n")

driver.execute_script("window.scrollTo(0, 0);")

while True:
    # Scroll down to bottom
    driver.execute_script(
        "window.scrollTo(0, document.documentElement.scrollHeight);")

    # Wait to load page
    time.sleep(2)
    # reply_button_xpath = "//ytd-button-renderer[@id='more-replies']/a/paper button[@id='button']"
    # r = driver.find_elements(By.XPATH, reply_button_xpath)
    # r[0].click()
    # Find all reply buttons
    # reply_buttons = driver.find_elements(
    #     By.XPATH,
    #     "//ytd-button-renderer[@id='more-replies']/a/paper-button[@id='button']")
    # Calculate new scroll height and compare with last scroll height

    reply_buttons = driver.find_elements(
        By.XPATH, '//*[@id="more-replies"]'
    )  #'//*[@id="more-replies"]/yt-button-shape/button')
    # # Click each reply button that hasn't been clicked yet
    for button in reply_buttons:
        #     # if button.is_enabled() and button.is_displayed():
        #     # driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(1)

    #     if button.is_enabled():
    #         button.click()
    new_height = driver.execute_script(
        "return document.documentElement.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

for _ in range(35):  # adjust this range to control the number of scrolls
    scroll_height = driver.execute_script(
        "return document.documentElement.scrollHeight;")
    scroll_up_amount = scroll_height * 0.02  # 10% of the page height
    driver.execute_script(
        f"window.scrollTo(0, document.documentElement.scrollTop - {scroll_up_amount});"
    )

comments_xpath = '//*[@id="content-text"]'
comments_andsubreplies = driver.find_elements(By.XPATH, comments_xpath)
with open("comments_with_sr.txt", "w") as file:
    for comment_sr in comments_andsubreplies:
        # file.write("Comment: " + comment_sr.text + "\n")
        file.write(comment_sr.text + "\n")

sys.exit()

# XPath expressions for comments, sub-replies, and likes
comments_xpath = '//*[@id="content-text"]'
#sub_replies_xpath = '//*[@id="content-text"]/span/text()'#'//*[@id="content-text"]/span'#'//*[@id="content-text"]/following-sibling::div[@id="more-replies"]'
sub_replies_xpath = '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-comments/ytd-item-section-renderer/div[3]/ytd-comment-thread-renderer[1]/div/ytd-comment-replies-renderer/div[1]/div[2]/div[1]/ytd-comment-view-model[1]/div[3]/div[2]/ytd-expander/div/yt-attributed-string'
likes_xpath = '//*[@id="vote-count-middle"]'

reply_button_txt_content = '//*[@id="more-replies"]/yt-button-shape/button/div[2]'

rs = "/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-comments/ytd-item-section-renderer/div[3]/ytd-comment-thread-renderer[3]/div/ytd-comment-replies-renderer/div[1]/div[2]/div[1]/ytd-comment-view-model[1]/div[3]/div[2]/ytd-expander/div/yt-attributed-string/span"

# reply_buttons = driver.find_elements(By.ID, "more-replies")
# reply_buttons = driver.find_elements(By.XPATH,'//*[@id="more-replies"]/yt-button-shape/button')
# # Click each reply button that hasn't been clicked yet
# for button in reply_buttons:
#     # if button.is_enabled() and button.is_displayed():
#     # driver.execute_script("arguments[0].scrollIntoView(true);", button)
#     button.click()
#'/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-comments/ytd-item-section-renderer/div[3]/ytd-comment-thread-renderer[1]/div/ytd-comment-replies-renderer/div[1]/div[2]/div[1]/ytd-comment-view-model[1]/div[3]/div[2]/ytd-expander/div/yt-attributed-string'
print("Hol up")
time.sleep(10)
#driver.find_elements_by_xpath("//ytd-button-renderer[@id='more-replies']/a/paper-button[@id='button']").click()
# Find all comments, sub-replies, and likes
comments = driver.find_elements(By.XPATH, comments_xpath)
sub_replies = driver.find_elements(By.XPATH, sub_replies_xpath)
likes = driver.find_elements(By.XPATH, likes_xpath)

print(sub_replies)
# Create a dictionary to store comments and their corresponding sub-replies and likes
comment_data = {}

# Iterate over comments and extract sub-replies and likes
for i, comment in enumerate(comments):
    comment_text = comment.text
    sub_reply_text = ''
    like_text = ''

    # Check if sub-replies exist for the current comment
    if i < len(sub_replies):
        sub_reply_text = sub_replies[i].text

    # Check if likes exist for the current comment
    if i < len(likes):
        like_text = likes[i].text

    # Store comment data in the dictionary
    comment_data[comment_text] = {
        'sub_reply': sub_reply_text,
        'likes': like_text
    }

for sub_reply in sub_replies:
    print(sub_reply.text)

# comments = driver.find_elements(By.XPATH, comments_xpath)
# sub_replies = driver.find_elements(By.XPATH, sub_replies_xpath)

# for i, comment in enumerate(comments):
#     comment_text = comment.text
#     sub_reply_text = ''

#     if i < len(sub_replies):
#         sub_reply_text = sub_replies[i].text

#     print(f"Comment: {comment_text}")
#     print(f"Sub-reply: {sub_reply_text}\n")

# Write comment data to a file
with open('output_test.txt', 'w') as file:
    for comment, data in comment_data.items():
        file.write(f"Comment: {comment}\n")
        file.write(f"Sub-reply: {data['sub_reply']}\n")
        file.write(f"Likes: {data['likes']}\n\n")

print("DONE MBB 4Real")
