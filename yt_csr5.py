import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# from tqdm import tqdm
import re
import sys
from alive_progress import alive_bar
from bs4 import BeautifulSoup, NavigableString

ALL_COMMENTS_XPATH = '//*[@id="content-text"]'
REPLY_BUTTON_XPATH = '//*[@id="more-replies"]'
SHOW_MORE_REPLIES_BUTTON_XPATH = "//button[@aria-label='Show more replies']"
SCROLL_PAUSE_TIME = 0.5 # seconds
PG_LOAD_PAUSE_TIME = 5 # seconds


def get_video_id_from_url(url):
    video_id = re.search(r"v=([^&]*)", url).group(1)
    #print(video_id)
    return video_id


def get_url_from_video_id(video_id):
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    return video_url


def scrape_video_ids_from_playlist(url, driver_headless=True):
    """
    Scrape video IDs from a YouTube playlist.

    Args:
        url (str): URL of the YouTube playlist.

    Returns:
        list: List of video IDs.
    """
    # Initialize the driver
    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    if driver_headless:
        chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    js_code = """
        var els = document.getElementsByClassName('yt-simple-endpoint style-scope ytd-playlist-video-renderer');
        var show="";
        for(i = 0;i<els.length;i++){
            var el = els[i];
            show += (el.href.split('?v=')[1].split('&list')[0] + "\\n");
        }
        return show;
    """
    WAIT_TILL_LOADED = 2
    video_ids_list = []
    steps = [
        "Loading YouTube playlist", "Scrolling to the bottom of the page",
        "Executing JavaScript code & Writing video IDs to file"
    ]
    for step in tqdm(steps, desc="Scraping video IDs"):
        if step == "Loading YouTube playlist":
            # time.sleep(6)
            time.sleep(WAIT_TILL_LOADED)
        elif step == "Scrolling to the bottom of the page":
            driver.execute_script(
                "window.scrollTo(0, document.documentElement.scrollHeight);")
            # time.sleep(6)
            time.sleep(WAIT_TILL_LOADED)
        elif step == "Executing JavaScript code & Writing video IDs to file":
            video_ids = driver.execute_script(js_code)  # returns str
            # write video ids to file
            if video_ids == "":
                raise ValueError("No video IDs found in the playlist")
            else:
                with open("plvids.txt", "w") as file:
                    file.write(video_ids + "\n")

            video_ids_list = video_ids.splitlines()
        # elif step == "Writing video IDs to file":
        #     if video_ids:
        #         with open("plvids.txt", "w") as file:
        #             file.writelines(vid + "\n" for vid in video_ids)
        #     else:
        #         raise ValueError("No video IDs found in the playlist")
        #     driver.quit()
        # print("** Scraped video IDs from YouTube playlist")

    print("Video Ids From Playlist:")
    print(video_ids_list)
    return video_ids_list



##### UTILS
def get_text_with_emojis(element):
    text_content = ""
    for child in element.children:
        if isinstance(child, str):
            text_content += str(child)
        elif child.name == "img":
            text_content += child["alt"]
        elif child.name == "span":
            text_content += get_text_with_emojis(child)
    return text_content


def save_comments(contents, units, jsonl_filename, json_filename):
    """Saves comments to JSONL and JSON files."""
    print(f"Saving {units} to JSON and JSONL files....")
    
    assert units in ["top-level comments", "top-level comments and their subreplies"], f"Invalid units: {units}.. src code bug detected!"


    # Extract comment texts (including emojis)
    comment_texts = []
    for comment in contents:
        html_content = comment.get_attribute("innerHTML")
        soup = BeautifulSoup(html_content, "html.parser")
        text_with_emojis = get_text_with_emojis(soup)
        comment_texts.append(text_with_emojis)

    # Save comments to JSONL file
    with open(jsonl_filename, "w", encoding="utf-8") as jsonl_file:
        for text in comment_texts:
            json.dump({"text": text}, jsonl_file, ensure_ascii=False)
            jsonl_file.write("\n")

    # Save comments to JSON file
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(comment_texts, json_file, indent=4, ensure_ascii=False)

    print(f"-> Saved {len(comment_texts)} {units} to {jsonl_filename} & {json_filename}")
        # with open(jsonl_filename, "w") as jsonl_file, open(json_filename, "w") as json_file:
        #     for comment in contents:
        #         jsonl_file.write(json.dumps(comment.text) + "\n")
        #     json.dump(contents.text, json_file, indent=4)


######



class YTScraper:

    def __init__(self, headless=False, incognito=False):
        try:
            options = ChromeOptions()

            if not isinstance(headless, bool) or not isinstance(incognito, bool):
                raise TypeError("headless and incognito must be boolean values")

            if incognito:
                options.add_argument('--incognito')
            if headless:
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')

            self.driver = webdriver.Remote(
                command_executor='http://localhost:4444',
                options=options
            )
        except TypeError as e:
            logging.error(f"Invalid argument type: {e}")
            raise
        except WebDriverException as e:
            logging.error(f"Failed to create WebDriver instance: {e}")
            raise
        except (URLError, ConnectionRefusedError) as e:
            logging.error(f"Connection issue with Selenium Grid: {e}")
            raise

    def match_comments_json_new(comments_data, jsonl_file, output_file, json_file, json_lines_file):
        """
            Match the original comments with their corresponding sub-replies.

            Args:
                comments_data (list): List of dictionaries containing top-level comment text and number of subreplies.
                jsonl_file (str): Path to the JSONL file containing all comments and subreplies.
                output_file (str): Path to the output file.
                json_file (str): Path to the JSON output file.
                json_lines_file (str): Path to the JSON lines output file.

            Returns:
                None
        """
        print("Matching Comments with their Subreplies....")
        # Read the JSONL file into a list of dictionaries
        # Read the JSONL file into a list of dictionaries
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            all_comments = [json.loads(line) for line in f.readlines()]

        # Initialize an empty dictionary to store the comments and their sub-replies
        comment_replies = {}

        # Iterate over the all_comments list
        i = 0
        while i < len(all_comments):
            comment_text = all_comments[i]['text']

            # Check if the comment is a top-level comment with subreplies
            if any(comment_data['text'] == comment_text for comment_data in comments_data):
                # Find the corresponding comment data
                comment_data = next(comment_data for comment_data in comments_data if comment_data['text'] == comment_text)
                num_subreplies = comment_data['num_subreplies']

                # Extract the subreplies
                end_index = min(i + 1 + num_subreplies, len(all_comments))
                subreplies = [all_comments[j]['text'] for j in range(i + 1, end_index)]

                # Store the comment and its subreplies in the dictionary
                comment_replies[comment_text] = subreplies

                # Skip the subreplies
                i += num_subreplies + 1
            else:
                # If the comment is not a top-level comment with subreplies, add it to the dictionary with an empty list of subreplies
                comment_replies[comment_text] = []
                i += 1

        # Open the output file for writing
        with open(output_file, 'w') as f:
            # Iterate over the comment_replies dictionary
            for comment, subreplies in comment_replies.items():
                # Write the original comment with '>' symbol
                f.write(f"> {comment}\n")

                # Write the subreplies with indentation
                for subreply in subreplies:
                    f.write(f"  {subreply}\n")

        # Create a JSON-compatible dictionary
        json_data = [{
            "original_comment": comment,
            "subreplies": subreplies
        } for comment, subreplies in comment_replies.items()]

        # Open the JSON file for writing
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

        # Open the JSON lines file for writing
        with open(json_lines_file, 'w', encoding='utf-8') as f:
            for item in json_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"-> Saved MATCHED Comments with their Subreplies to files {json_lines_file} and {json_file}")
    
    # @staticmethod
    # def save_comments(contents, jsonl_filename, json_filename):
    #     """Saves comments to JSONL and JSON files."""

    #     with alive_bar(title="Writing to JSON and JSONL files",
    #                    stats=True) as bar:

    #         # Extract comment texts
    #         comment_texts = [comment.text for comment in contents]

    #         # Save comments to JSONL file
    #         with open(jsonl_filename, "w") as jsonl_file:
    #             for text in comment_texts:
    #                 json.dump({"text": text}, jsonl_file)
    #                 jsonl_file.write("\n")
    #                 bar()

    #         # Save comments to JSON file
    #         with open(json_filename, "w") as json_file:
    #             json.dump(comment_texts, json_file, indent=4)

    #     # with open(jsonl_filename, "w") as jsonl_file, open(json_filename, "w") as json_file:
    #     #     for comment in contents:
    #     #         jsonl_file.write(json.dumps(comment.text) + "\n")
    #     #     json.dump(contents.text, json_file, indent=4)

    # TODO: add try except blocks
    def get_all_comments_and_subreplies_using_url(self, url):
        print(f"** Starting to Scrape Comments & Subreplies for {url} **\n")
        start_time = time.time()

        video_id = get_video_id_from_url(url)
        self.driver.get(url)

        toplvl_comments_only_filename_txt = f'toplvl_comments_only_{video_id}.txt'
        toplvl_comments_only_filename_json = f'toplvl_comments_only_{video_id}.json'
        toplvl_comments_only_filename_jsonl = f'toplvl_comments_only_{video_id}.jsonl'

        toplvl_comments_with_sr_filename_txt = f'toplvl_comments_with_sr_{video_id}.txt'
        toplvl_comments_with_sr_filename_json = f'toplvl_comments_with_sr_{video_id}.json'
        toplvl_comments_with_sr_filename_jsonl = f'toplvl_comments_with_sr_{video_id}.jsonl'

        matched_filename_txt = f'matched_comments_with_sr_{video_id}.txt'
        matched_filename_json = f'matched_comments_with_sr_{video_id}.json'
        matched_filename_jsonl = f'matched_comments_with_sr_{video_id}.jsonl'








        # R&D on finding the num_subreplies asssociated with each comment
        # time.sleep(10)
        # reply_buttons = self.driver.find_elements(By.XPATH, REPLY_BUTTON_XPATH)

        # # Create a list to store the comment data
        # comments_data = []

        # # Click each reply button that hasn't been clicked yet
        # with alive_bar(len(reply_buttons), title="Expanding subreplies", force_tty=True) as bar:
        #     for button in reply_buttons:
        #         # Position the button near the top of the viewport
        #         self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", button)
        #         self.driver.execute_script("window.scrollBy(0, -300);", button)  # adjust the offset as needed
        #         time.sleep(0.25)

        #         # Get the comment corresponding to the reply button
        #         comment_xpath = "ancestor::ytd-comment-thread-renderer/descendant::ytd-comment-view-model"
        #         comment_element = button.find_element(By.XPATH, comment_xpath)
        #         comment_text = comment_element.find_element(By.ID, "content-text").text
                

        #         # Extract the number of replies from the button
        #         num_replies_text = button.find_element(By.XPATH, ".//span[@role='text']").text
        #         num_replies = int(''.join(filter(str.isdigit, num_replies_text)))

        #         # Store the comment data
        #         comment_data = {"text": comment_text, "num_subreplies": num_replies}
        #         comments_data.append(comment_data)
        #         print(f"here: {comment_text} and {num_replies}")


        #         self.driver.execute_script("arguments[0].click();", button)
        #         time.sleep(0.5)
        #         bar()  # increment the progress bar
                
        # # Print the comment data
        # print("bs dnnn")
        # print(comments_data)

        # time.sleep(500)
        # sys.exit()


        # Get scroll height
        last_height = self.driver.execute_script(
            "return document.documentElement.scrollHeight")

        # pbar = tqdm(total=float('inf'), desc="Scrolling through comments")
        # pbar = tqdm(desc="Scrolling through comments", unit=" scrolls", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{percentage:.0f}%]")
        num_toplvl_comments_so_far_old = 0
        with alive_bar(title="Gathering only top-level comments",
                       stats=True, force_tty=True,
                       unit=" top-level comments") as bar:
            while True:
                # Scroll down to bottom
                self.driver.execute_script(
                    "window.scrollTo(0, document.documentElement.scrollHeight);"
                )

                # Wait to load page
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = self.driver.execute_script(
                    "return document.documentElement.scrollHeight")
                if new_height == last_height:
                    time.sleep(PG_LOAD_PAUSE_TIME) # Give time for page to load
                    # double check mechanism
                    new_height = self.driver.execute_script(
                    "return document.documentElement.scrollHeight")
                    if new_height == last_height: # if they are still the same, then we break
                        break
                last_height = new_height
                
                toplvl_comments_so_far = self.driver.find_elements(By.XPATH,
                                                    ALL_COMMENTS_XPATH)
                num_toplvl_comments_so_far_new = len(toplvl_comments_so_far) 
                bar(num_toplvl_comments_so_far_new - num_toplvl_comments_so_far_old)
                # bar.text(f'-> {bar.current} top-level comments collected')
                num_toplvl_comments_so_far_old = num_toplvl_comments_so_far_new
                # pbar.update(1)  # Update the progress bar
            # pbar.close()  # Close the progress bar



        # EXTRACT AND SAVE TOPLVL COMMENTS ONLY
        toplvl_comments_all = self.driver.find_elements(By.XPATH,
                                                    ALL_COMMENTS_XPATH)
        print(f"-> Gathered {len(toplvl_comments_all)} top-level comments")
        # with open(toplvl_comments_only_filename_txt, "w") as file:
        #     for c in toplvl_comments:
        #         file.write(c.text + "\n")
        save_comments(toplvl_comments_all, "top-level comments",
                            toplvl_comments_only_filename_jsonl,
                            toplvl_comments_only_filename_json)



        # self.driver.execute_script("window.scrollTo(0, 0);")
        # time.sleep(SCROLL_PAUSE_TIME)

        # # Add another progress bar for scrolling through reply buttons
        # # pbar = tqdm(total=float('inf'), desc="Expanding reply buttons")
        # with alive_bar(title="Gathering comments & subreplies",
        #                stats=True) as bar:
        #     while True:
        #         # Scroll down to bottom
        #         self.driver.execute_script(
        #             "window.scrollTo(0, document.documentElement.scrollHeight);"
        #         )

        #         # Wait to load page
        #         time.sleep(SCROLL_PAUSE_TIME)
        #         reply_buttons = self.driver.find_elements(
        #             By.XPATH, REPLY_BUTTON_XPATH)
        #         # Click each reply button that hasn't been clicked yet
        #         for button in reply_buttons:
        #             self.driver.execute_script("arguments[0].click();", button)
        #             # time.sleep(1)

        #         #     if button.is_enabled():
        #         #         button.click()
        #         new_height = self.driver.execute_script(
        #             "return document.documentElement.scrollHeight")
        #         if new_height == last_height:
        #             break
        #         print(f'{last_height}, {new_height}')
        #         last_height = new_height
        #         bar()
        #         bar.text(f'-> {bar.current} scrolls')
        #         # pbar.update(1)  # Update the progress bar
        # # pbar.close()  # Close the progress bar





        reply_buttons = self.driver.find_elements(By.XPATH, REPLY_BUTTON_XPATH)
        # Create a list to store the toplvl comment data (comment text and num sub replies)
        toplvl_comments_data = []
        # Click each reply button that hasn't been clicked yet
        with alive_bar(len(reply_buttons), title="Expanding subreplies", force_tty=True) as bar:
            for button in reply_buttons:
                # Position the button near the top of the viewport
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", button)
                self.driver.execute_script("window.scrollBy(0, -300);", button)  # adjust the offset as needed
                time.sleep(0.25)

                # Get the comment text (including any possible emojis) corresponding to the reply button
                comment_xpath = "ancestor::ytd-comment-thread-renderer/descendant::ytd-comment-view-model"
                comment_element = button.find_element(By.XPATH, comment_xpath)
                comment_html = comment_element.find_element(By.ID, "content-text").get_attribute("innerHTML")
                comment_text = get_text_with_emojis(BeautifulSoup(comment_html, "html.parser"))
                                

                # Extract the number of replies from the button
                num_replies_text = button.find_element(By.XPATH, ".//span[@role='text']").text
                num_replies = int(''.join(filter(str.isdigit, num_replies_text)))

                # Store the comment data
                comment_data = {"text": comment_text, "num_subreplies": num_replies}
                toplvl_comments_data.append(comment_data)
                print(f"here: {comment_text} and {num_replies}")


                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(0.5)
                bar()  # increment the progress bar


        # VERY SOLID
        # reply_buttons = self.driver.find_elements(By.XPATH, REPLY_BUTTON_XPATH)

        # # Click each reply button that hasn't been clicked yet
        # with alive_bar(len(reply_buttons), title="Expanding subreplies", force_tty=True) as bar:
        #     for button in reply_buttons:
        #         # Position the button near the top of the viewport
        #         self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", button)
        #         self.driver.execute_script("window.scrollBy(0, -200);", button)  # adjust the offset as needed
        #         self.driver.execute_script("arguments[0].click();", button)
        #         time.sleep(0.5)
        #         bar()  # increment the progress bar


        # GOOD
        # reply_buttons = self.driver.find_elements(By.XPATH, REPLY_BUTTON_XPATH)
        # # Click each reply button that hasn't been clicked yet
        # with alive_bar(len(reply_buttons), title="Expanding subreplies") as bar:
        #     for button in reply_buttons:
        #         self.driver.execute_script("arguments[0].click();", button)
        #         time.sleep(0.02)
        #         bar()  # increment the progress bar
            
        # for _ in range(100):  # adjust this range to control the number of scrolls
        #     scroll_height = self.driver.execute_script(
        #         "return document.documentElement.scrollHeight;")
        #     scroll_up_amount = scroll_height * 0.01  # 1% of the page height
        #     self.driver.execute_script(
        #         f"window.scrollTo(0, document.documentElement.scrollTop - {scroll_up_amount});"
        #     )
        #     time.sleep(0.5)

        # scroll_percentage = 0.01 # 1%
        # num_scroll_iterations = int(1 / scroll_percentage)
        # with alive_bar(num_scroll_iterations, title="Gathering subreplies") as bar:
        #     for _ in range(num_scroll_iterations):  
        #         scroll_height = self.driver.execute_script("return document.documentElement.scrollHeight;")
        #         scroll_up_amount = scroll_height * scroll_percentage  
        #         self.driver.execute_script(f"window.scrollTo(0, document.documentElement.scrollTop - {scroll_up_amount});")
        #         time.sleep(0.5)
        #         bar()  # increment the progress bar
        #         bar.text(f'-> ~{bar.current}% of subreplies gathered')

        # while True:
        #     showmore_buttons = self.driver.find_elements(By.XPATH, "//button[@aria-label='Show more replies']")
        #     numb_show_more_replies_buttons = len(showmore_buttons)
        #     if numb_show_more_replies_buttons == 0:
        #         break
        #     print(showmore_buttons)

        #     # Click each reply button that hasn't been clicked yet
        #     with alive_bar(numb_show_more_replies_buttons, title="Expanding Show More Replies Buttons") as bar:
        #         for button in showmore_buttons:
        #             # Scroll to the button before clicking
        #             self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        #             self.driver.execute_script("arguments[0].click();", button)
        #             time.sleep(0.02)
        #             bar()  # increment the progress bar

        #     time.sleep(3)
        
        
        while True:
            # showmore_buttons = self.driver.find_elements(By.XPATH, "//button[@aria-label='Show more replies']")
            show_more_replies_buttons = self.driver.find_elements(By.XPATH, SHOW_MORE_REPLIES_BUTTON_XPATH)
            numb_show_more_replies_buttons = len(show_more_replies_buttons)
            if numb_show_more_replies_buttons == 0:
                break

            print(show_more_replies_buttons)

            # Click each reply button that hasn't been clicked yet
            with alive_bar(numb_show_more_replies_buttons, title="Expanding Show More Replies Buttons") as bar:
                for button in show_more_replies_buttons:
                     # Position the button near the top of the viewport
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", button)
                    self.driver.execute_script("window.scrollBy(0, -200);", button)  # adjust the offset as needed
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(0.5)
                    bar()  # increment the progress bar

            time.sleep(5)
    
        # scroll to the bottom
        self.driver.execute_script(
                    "window.scrollTo(0, document.documentElement.scrollHeight);"
                )
        time.sleep(2)      

        # pause_time = 5 #secs
        # print(f"Intentionally pausing for {pause_time} seconds")
        # time.sleep(pause_time)

        # scroll_amount = 1000  # pixels
        # scroll_smoothness = 10  # Increase this value for smoother scrolling
        # scroll_delay = 0.05  # seconds
    
        # scroll_height = self.driver.execute_script("return document.documentElement.scrollHeight;")
        # num_scroll_iterations = int(scroll_height / scroll_amount)

        # with alive_bar(num_scroll_iterations, title="Gathering subreplies") as bar:
        #     for _ in range(num_scroll_iterations):
        #         # Smooth scrolling
        #         for _ in range(scroll_smoothness):
        #             self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollTop - " + str(scroll_amount // scroll_smoothness) + ");")
        #             time.sleep(scroll_delay)
        #         bar()  # increment the progress bar
        #         bar.text(f'-> {int((bar.current / num_scroll_iterations) * 100)}% of subreplies gathered')
       



        ###### PERCENTAGE BASED SCROLLING ######
        # scroll_percentage = 0.01  # 1%
        # num_scroll_iterations = int(1 / scroll_percentage)
        # scroll_smoothness = 10  # Increase this value for smoother scrolling

        # with alive_bar(num_scroll_iterations * scroll_smoothness, title="Gathering subreplies") as bar:
        #     for _ in range(num_scroll_iterations):
        #         scroll_height = self.driver.execute_script("return document.documentElement.scrollHeight;")
        #         scroll_up_amount = scroll_height * scroll_percentage

        #         # Smooth scrolling
        #         for _ in range(scroll_smoothness):
        #             self.driver.execute_script(f"window.scrollTo(0, document.documentElement.scrollTop - {scroll_up_amount / scroll_smoothness});")
        #             time.sleep(0.05)  # Adjust this value to control the scrolling speed
        #             bar()  # increment the progress bar
        #             bar.text(f'-> ~{bar.current}% of subreplies gathered')
        ###### PERCENTAGE BASED SCROLLING ######
                
        # time.sleep(5)
        # EXTRACT AND SAVE BOTH COMMENTS AND SUBREPLIES
        comments_and_subreplies = self.driver.find_elements(
            By.XPATH, ALL_COMMENTS_XPATH)
        # with open(toplvl_comments_with_sr_filename_txt, "w") as file:
        #     for comment_sr in comments_and_subreplies:
        #         # file.write("Comment: " + comment_sr.text + "\n")
        #         file.write(comment_sr.text + "\n")
        print(f"-> Gathered {len(comments_and_subreplies)} top-level comments and their subreplies")
        save_comments(comments_and_subreplies, "top-level comments and their subreplies",
                                toplvl_comments_with_sr_filename_jsonl,
                                toplvl_comments_with_sr_filename_json)

        # match the toplvl comments with their corresponding subreplies
        # YTScraper.match_comments(toplvl_comments_only_filename_txt,
        #                          toplvl_comments_with_sr_filename_txt,
        #                          matched_filename_txt, 
        #                          matched_filename_json,
        #                          matched_filename_jsonl)
        
        # match the toplvl comments with their corresponding subreplies
        # YTScraper.match_comments_json(toplvl_comments_only_filename_jsonl,
        #                               toplvl_comments_with_sr_filename_jsonl,
        #                               matched_filename_txt, 
        #                               matched_filename_json,
        #                               matched_filename_jsonl)
        YTScraper.match_comments_json_new(toplvl_comments_data,
                                      toplvl_comments_with_sr_filename_jsonl,
                                      matched_filename_txt, 
                                      matched_filename_json,
                                      matched_filename_jsonl)

        
        end_time = time.time()
        total_execution_time = end_time - start_time
        print(f"\n** Finished Scraping Comments & Subreplies for {url} in {total_execution_time} seconds **\n")


    def get_all_comments_and_subreplies_using_video_id(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        self.get_all_comments_and_subreplies_using_url(url)


if __name__ == "__main__":
    example_url = "https://www.youtube.com/watch?v=Kflgwacs0J8"
    scraper = YTScraper()
    scraper.get_all_comments_and_subreplies_using_url(example_url)




###### OLD MATCHING ALGOS ######

# FIRST ALGO FOR TXT FILE MATCHING
#    @staticmethod
#     def match_comments(orig_file, reply_file, output_file, json_file,
#                        json_lines_file):
#         """
#             Match the original comments with their corresponding sub-replies.

#             Args:
#                 orig_file (str): Path to the file containing the original comments.
#                 reply_file (str): Path to the file containing the original comments with sub-replies.
#                 output_file (str): Path to the output file.
#                 json_file (str): Path to the JSON output file.
#                 json_lines_file (str): Path to the JSON lines output file.

#             Returns:
#                 None
#             """
#         # Read the original comments into a list
#         with open(orig_file, 'r') as f:
#             orig_comments = [line.strip() for line in f.readlines()]

#         # Read the reply file into a list of lines
#         with open(reply_file, 'r') as f:
#             reply_lines = [line.strip() for line in f.readlines()]

#         # Initialize an empty dictionary to store the comments and their sub-replies
#         comment_replies = {}

#         # Initialize an index to keep track of the current original comment
#         comment_index = 0

#         # Open the output file for writing
#         with open(output_file, 'w') as f:
#             # Iterate over the reply lines
#             for line in reply_lines:
#                 # If the line matches the current original comment, add it to the dictionary
#                 if line == orig_comments[comment_index]:
#                     comment_replies[line] = []
#                     f.write(f"> {line}\n"
#                             )  # Write original comment with '>' symbol
#                 # If the line is a sub-reply, add it to the list of sub-replies for the current original comment
#                 elif line in orig_comments:
#                     comment_index += 1
#                     comment_replies[line] = []
#                     f.write(f"> {line}\n"
#                             )  # Write original comment with '>' symbol
#                 else:
#                     comment_replies[orig_comments[comment_index]].append(line)
#                     f.write(f"      {line}\n")  # Write sub-reply with indentation

#         # Create a JSON-compatible dictionary
#         json_data = [{
#             "original_comment": comment,
#             "subreplies": replies
#         } for comment, replies in comment_replies.items()]

#         # Open the JSON file for writing
#         with open(json_file, 'w') as f:
#             json.dump(json_data, f, indent=4)

#         # Open the JSON lines file for writing
#         with open(json_lines_file, 'w') as f:
#             for item in json_data:
#                 f.write(json.dumps(item) + "\n")

# 2nd ALGO FOR JSON FILE MATCHING
    # def match_comments_json(jsonl_file1, jsonl_file2, output_file, json_file, json_lines_file):
    #     """
    #         Match the original comments with their corresponding sub-replies.

    #         Args:
    #             jsonl_file1 (str): Path to the first JSONL file.
    #             jsonl_file2 (str): Path to the second JSONL file.
    #             output_file (str): Path to the output file.
    #             json_file (str): Path to the JSON output file.
    #             json_lines_file (str): Path to the JSON lines output file.

    #         Returns:
    #             None
    #     """
    #     print("Matching Comments with their Subreplies....")
    #     # Read the first JSONL file into a list of dictionaries
    #     with open(jsonl_file1, 'r') as f:
    #         orig_comments = [json.loads(line) for line in f.readlines()]

    #     # Read the second JSONL file into a list of dictionaries
    #     with open(jsonl_file2, 'r') as f:
    #         reply_lines = [json.loads(line) for line in f.readlines()]

    #     # Initialize an empty dictionary to store the comments and their sub-replies
    #     comment_replies = {}

    #     # Initialize an index to keep track of the current original comment
    #     comment_index = 0

    #     # OLD CODE (NOT GOOD OR EFFICIENT LOGIC)
    #     # # Open the output file for writing
    #     # with open(output_file, 'w') as f:
    #     #     # with alive_bar(title="Matching Toplevel Comments with Subreplies",
    #     #     #     stats=True) as bar:
    #     #         # Iterate over the reply lines
    #     #         for line in reply_lines:
    #     #             # If the line matches the current original comment, add it to the dictionary
    #     #             if line['text'] == orig_comments[comment_index]['text']:
    #     #                 comment_replies[line['text']] = []
    #     #                 f.write(f"> {line['text']}\n")  # Write original comment with '>' symbol
    #     #             # If the line is a sub-reply, add it to the list of sub-replies for the current original comment
    #     #             elif line['text'] in [comment['text'] for comment in orig_comments]:
    #     #                 comment_index += 1
    #     #                 comment_replies[line['text']] = []
    #     #                 f.write(f"> {line['text']}\n")  # Write original comment with '>' symbol
    #     #             else:
    #     #                 comment_replies[orig_comments[comment_index]['text']].append(line['text'])
    #     #                 f.write(f"  {line['text']}\n")  # Write sub-reply with indentation
    #     #             # bar()

    #     # THIS MATCHING COMMENTS LOGIC ONLY WORKS IF THERE ARE NO SUBREPLIES THAT EXACTLY MATCH THE TOPLVL COMMENT RIGHT AFTER IT
    #     # Open the output file for writing
    #     num_top_lvl_comments = len(orig_comments)
    #     if(num_top_lvl_comments == 0):
    #         print("No top-level comments to match...done")
    #         return
    #     with open(output_file, 'w') as f:
    #         # with alive_bar(title="Matching Toplevel Comments with Subreplies",
    #         #     stats=True) as bar:

    #             # Initialize the first toplvl comment as such                
    #             current_top_lvl_comment = orig_comments[comment_index]['text'] # ASSERT at least one toplvl comment exists
    #             next_toplvl_commment = orig_comments[comment_index+1]['text'] if comment_index+1 < num_top_lvl_comments else None
    #             comment_replies[current_top_lvl_comment] = []
    #             f.write(f"> {current_top_lvl_comment}\n")  # Write original comment with '>' symbol

    #             # Iterate over the reply lines
    #             for line in reply_lines[1:]:
    #                 # If the line matches the next original (toplvl) comment, add it to the dictionary
    #                 if line['text'] == next_toplvl_commment and next_toplvl_commment is not None:
    #                     # keep in mind that line['text'] is literally next_toplvl_commment
    #                     comment_index += 1
    #                     comment_replies[line['text']] = []
    #                     f.write(f"> {line['text']}\n")  # Write original comment with '>' symbol

    #                     current_top_lvl_comment = next_toplvl_commment
    #                     next_toplvl_commment = next_toplvl_commment = orig_comments[comment_index+1]['text'] if comment_index+1 < num_top_lvl_comments else None
    #                 else:
    #                     # the two lines below are effectively the same
    #                     # comment_replies[orig_comments[comment_index]['text']].append(line['text'])
    #                     comment_replies[current_top_lvl_comment].append(line['text'])
    #                     f.write(f"  {line['text']}\n")  # Write sub-reply with indentation
    #                 # bar()

    #     # Create a JSON-compatible dictionary
    #     json_data = [{
    #         "original_comment": comment,
    #         "subreplies": replies
    #     } for comment, replies in comment_replies.items()]

    #     # Open the JSON file for writing
    #     with open(json_file, 'w') as f:
    #         json.dump(json_data, f, indent=4)

    #     # Open the JSON lines file for writing
    #     with open(json_lines_file, 'w') as f:
    #         for item in json_data:
    #             f.write(json.dumps(item) + "\n")
    #     print(f"-> Saved MATCHED Comments with their Subreplies to files {json_lines_file} and {json_file}")
    

    ###### OLD MATCHING ALGOS ######
