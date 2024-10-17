import time
import sys
import re
import requests
import sqlite3
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import urllib.robotparser
from urllib.parse import urlparse

# Say hello to the 'robots.txt' parser
rp = urllib.robotparser.RobotFileParser()

# Connect to the database
con = sqlite3.connect("searchindex.db")
cur = con.cursor()

# This list defines all status codes that are generally accepted by our script.
codes = requests.codes
good_status_codes = [codes.ok, codes.temporary_moved, codes.moved]

# Some default settings that can be changed by CLI arguments
keep_domain = False # Collect links only for initial domain
no_follow = False # Do not recurse into child links

# COLORS!!!
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

# Configure our chromium session settings
options = webdriver.ChromeOptions()
options.page_load_strategy = 'normal' # Wait until website fully loads
options.accept_insecure_certs = False
options.timeouts = { 'script': 10000, 'pageLoad' : 10000 } # Set a timeout to 5 seconds
options.unhandled_prompt_behavior = 'accept'
options.add_argument("--headless='new' --incognito --disable-features=Translate --disable-extensions --mute-audio --no-default-browser-check --no-first-run --disable-search-engine-choice-screen --deny-permission-prompts --disable-external-intent-requests --disable-notifications --enable-automation -blink-settings=imagesEnabled=false")


# Start session
driver = webdriver.Chrome(options=options)

def debug_wait():
    input("Press any key to continue... ")

def save(title, desc, link):
    print("---")
    print("title: "+BOLD+title+ENDC)
    print("desc:  "+BOLD+desc+ENDC)
    print("link:  "+BOLD+url_to_index+ENDC)
    print("---")
    now = datetime.datetime.utcnow()
    date = int(str(now.year)+str(now.month)+str(now.day))

    try:
        cur.execute("INSERT INTO 'searches' (title, desc, link, date) VALUES(?, ?, ?, ?)", (title, desc, link, date))
        con.commit()
        return
    except Exception as err:
        print(FAIL+"Database task failed. Cannot save because of an error: "+type(err).__name__+ENDC)
        time.sleep(1)
        save(title, desc, link)

first_iter = True

def goback():
    print("Going back...")
    global first_iter
    global url_to_index
    old_url = driver.current_url
    try:
        driver.back()
    except Exception as err:
        print(FAIL+"Driver can't go back: "+type(err).__name__+ENDC)
        exit(1)
    new_url = driver.current_url
    print("Old URL: "+old_url)
    print("New URL: "+new_url)
    if old_url == new_url or new_url == "data:,":
        print(FAIL+"No page to go back to!"+ENDC)
        exit(1)
    first_iter = True
    url_to_index=new_url

def exists(link):
    try:
        result = cur.execute("SELECT link FROM searches WHERE link=?", (link,))
        return len(cur.fetchall()) != 0
    except Exception as err:
        print(FAIL+"Database task failed. Cannot check existance because of an error: "+type(err).__name__+ENDC)
        time.sleep(1)
        exists(link)

# Create a database for searches if it doesn't exist yet
cur.execute("CREATE TABLE IF NOT EXISTS 'searches' ('id' integer primary key autoincrement unique not null, 'title' text not null, 'desc' text, 'link' text unique not null, 'date' integer not null, 'like' integer not null default 0, 'dislike' integer not null default 0)")

try:
    sys.argv[1]
except:
    print("Please, add an argument specifying the full URL to start crawling from like 'https://example.com'.")
    exit(1)

# This portion of code doesn't look good. Clean it up a bit later.
try:
    additional_arg = sys.argv[2]
    match additional_arg:
        case "keep_domain":
            keep_domain = True
        case "no_follow":
            no_follow = True
except:
    pass
try:
    additional_arg = sys.argv[2]
    match additional_arg:
        case "keep_domain":
            keep_domain = True
        case "no_follow":
            no_follow = True
except:
    pass
try:
    additional_arg = sys.argv[3]
    match additional_arg:
        case "keep_domain":
            keep_domain = True
        case "no_follow":
            no_follow = True
except:
    pass

url_to_index = sys.argv[1].lower().strip("/")
init_website = re.sub(r'^.*?://', '', url_to_index)
if keep_domain:
    print("Keeping domain:",init_website)

# Go to specified URL
while True:
    if url_to_index == "data:,":
        break
    print(OKBLUE+url_to_index+ENDC)
    try:
        driver.get(url_to_index)
    except TimeoutException:
        print(WARNING+"Timeout occured!"+ENDC)
        continue
    except Exception as err:
        print(FAIL+"Driver error occured: ("+type(err).__name__+")"+ENDC)
        # Go back in history
        goback()

    #driver.implicitly_wait(0.25)

    # Get title and description
    title = "Untitled"
    try:
        title = driver.title
        # Strip trailing newlines
        title = title.strip()
    except Exception as err:
        print(WARNING+"Failed to get contents of <title>: "+type(err).__name__+ENDC)

    if title == None:
        title = "Untitled"

    try:
        paragraph_tag = driver.find_element(By.TAG_NAME, "p").text
    except Exception as err:
        print(WARNING+"Failed to get contents of <p>: "+type(err).__name__+ENDC)
        paragraph_tag = ""
    try:
        header_tag = driver.find_element(By.TAG_NAME, "h1").text
    except Exception as err:
        print(WARNING+"Failed to get contents of <h1>: "+type(err).__name__+ENDC)
        header_tag = ""

    desc = ""
    if paragraph_tag != None or paragraph_tag != "":
        desc = paragraph_tag
    if header_tag != None or header_tag != "":
        desc = header_tag
    desc = desc.strip()

    # Save current website to the database
    # Skip saving (and do not print any error) if the script just started and website is already in db.
    if first_iter and exists(link=url_to_index):
        print("This site has been already added to the database but the script just started or went back from some weird page. It's probably okay to just skip saving and not bother.")
    else:
        save(title=title, desc=desc, link=url_to_index)

    # Reset first_iter to False
    if first_iter:
        print("Resetting first_iter to false...")
        first_iter = False

    # Get list of links
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
    except:
        print(WARNING+"No links found on this page"+ENDC)
        # Go back in history
        goback()

    # Remove duplicated values in list by converting it to a set and then going back to the list
    links = list(set(links))

    # Modify 'links' to only contain values of 'href' attributes
    index = 0
    while index < len(links):
        try:
            # Always convert the text to contains lowercase text
            # Remove trailing slash
            href = links[index].get_attribute("href").lower().strip("/")
            links[index] = href
            index+=1
        except:
            print("Failed to get 'href' attribute")
            links.pop(index)

    index = 0
    while index < len(links):
        if not links:
            break

        link = links[index]

        if link == None:
            print(FAIL+"No link in <a> tag!"+ENDC)
            links.pop(index)
            continue

        # Remove useless stuff (#, ?, &, :) from non-empty links
        link, sep, tail = link.partition('#')
        link, sep, tail = link.partition('?')
        link, sep, tail = link.partition('&')
        link, sep, tail = link.partition('%')
        links[index] = link

        print(link,'\b: ', end='')

        if link == "":
            print(FAIL+"Link is empty!"+ENDC)
            links.pop(index)
            continue

        if "javascript:" in link:
            print(FAIL+"Contains 'javascript:' text!"+ENDC)
            links.pop(index)
            continue

        if exists(link=link):
            print(WARNING+"Already indexed!"+ENDC)
            links.pop(index)
            continue

        if keep_domain and init_website not in link:
            print(WARNING+"Rejected by 'keep_domain' policy!"+ENDC)
            links.pop(index)
            continue

        # Check if the website behind the link is accessible.
        # For example, a link may point to non-existing website that returns 404 error code.
        # This is obviously bad. Skip it.
        try:
            response = requests.head(link, timeout=10, allow_redirects=True)
            status_code = int(response.status_code)
            content_type = response.headers['content-type']
            print(OKBLUE+"("+str(status_code)+") "+ENDC, end="")
            if "text/" not in content_type:
                print(FAIL+"Wrong content-type! ("+str(content_type)+")"+ENDC)
                links.pop(index)
                continue
            if status_code not in good_status_codes:
                print(FAIL+"Wrong status code!"+ENDC)
                links.pop(index)
                continue
        except Exception as err:
                print(FAIL+"Failed to connect ("+type(err).__name__+")"+ENDC)
                links.pop(index)
                continue

        # Nothing wrong until this point? The link seems to be good!
        print(OKGREEN+"OK"+ENDC)
        index+=1

    if not links:
        print(WARNING+"There are links on this page, but none of them are usefull."+ENDC)
        # Go back in history
        goback()
    else:
        if not no_follow:
            for link in links:
                url_to_index=link
        else:
            print("Not following any link. That's it")
            exit(0)

# End browser session
driver.quit()
