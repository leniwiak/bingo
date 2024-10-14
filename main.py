import sys
import requests
import sqlite3
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
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
options.timeouts = { 'script': 5000, 'pageLoad' : 5000 } # Set a timeout to 5 seconds
options.unhandled_prompt_behavior = 'accept'
options.add_argument("--incognito --disable-features=Translate --disable-extensions --mute-audio --no-default-browser-check --no-first-run --disable-search-engine-choice-screen --deny-permission-prompts --disable-external-intent-requests --disable-notifications --enable-automation -blink-settings=imagesEnabled=false")

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
    cur.execute("INSERT INTO searches (title, desc, link, date) VALUES(?, ?, ?, ?)", (title, desc, link, date))
    con.commit()

def exists(link):
    result = cur.execute("SELECT link FROM searches WHERE link=?", (link,))
    return len(cur.fetchall()) != 0

# Create a database for searches if it doesn't exist yet
cur.execute("CREATE TABLE IF NOT EXISTS 'searches' ('id' integer primary key autoincrement unique not null, 'title' text not null, 'desc' text, 'link' text unique not null, 'date' integer not null)")

try:
    sys.argv[1]
except:
    print("Please, add an argument specifying the full URL to start crawling from like 'https://example.com'.")
    exit(1)

url_to_index = sys.argv[1]
going_back = False


# Go to specified URL
while True:
    if url_to_index == "data:,":
        break
    print(OKBLUE+url_to_index+ENDC)
    if not going_back:
        try:
            driver.get(url_to_index)
        except Exception as err:
            print(FAIL+"Driver error: ("+type(err).__name__+")"+ENDC)
            # Go back in history
            old_url = driver.current_url
            driver.back()
            new_url = driver.current_url
            # Page did not change even after going back? That's not good... End the program.
            if old_url == new_url:
                print(FAIL+"There's no page to go back to!"+ENDC)
                break
            else:
                # Index previous website once again
                url_to_index=new_url
                # Singalize that we're going back
                going_back = True


    # Wait 2 seconds
    driver.implicitly_wait(0.5)

    # Get title and description
    title = driver.title
    if title == None:
        title = "Untitled"

    try:
        paragraph_tag = driver.find_element(By.TAG_NAME, "p")
    except:
        paragraph_tag = ""

    try:
        header_tag = driver.find_element(By.TAG_NAME, "h1")
    except:
        header_tag = ""

    if paragraph_tag != None or paragraph_tag != "":
        desc = paragraph_tag.text
    elif header_tag != None or header_tag != "":
        desc = header_tag.text
    else:
        desc = ""

    # Save current website to the database
    if not going_back:
        save(title=title, desc=desc, link=url_to_index)

    going_back = False

    # Get list of links
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
    except:
        print(WARNING+"No links found on this page"+ENDC)
        # Go back in history
        old_url = driver.current_url
        driver.back()
        new_url = driver.current_url
        # Page did not change even after going back? That's not good... End the program.
        if old_url == new_url:
            print(FAIL+"There's no page to go back to!"+ENDC)
            break
        else:
            # Index previous website once again
            url_to_index=new_url
            # Singalize that we're going back
            going_back = True


    # Modify 'links' to only contain values of 'href' attributes
    index = 0
    while index < len(links):
        try:
            href = links[index].get_attribute("href")
            links[index] = href
            index+=1
        except:
            print("Failed to get 'href' attribute")
            links.pop(index)

    index = 0
    while index < len(links):
        link = links[index]

        print(link,'\b: ', end='')

        if link == None:
            print(FAIL+"No link in <a> tag!"+ENDC)
            links.pop(index)
            continue

        # Remove useless stuff (#, ?, &) from non-empty links
        link, sep, tail = link.partition('#')
        link, sep, tail = link.partition('?')
        link, sep, tail = link.partition('&')
        links[index] = link

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

        # Check if the website behind the link is accessible.
        # For example, a link may point to non-existing website that returns 404 error code.
        # This is obviously bad. Skip it.
        try:
            status_code = requests.head(link, timeout=5)
            if status_code in good_status_codes:
                print(FAIL+"Returned wrong status code! ("+status_code+")"+ENDC)
                links.pop(index)
                continue
        except Exception as err:
                print(FAIL+"Failed to connect ("+type(err).__name__+")"+ENDC)
                links.pop(index)
                continue

        # Nothing wrong until this point? The link seems to be good!
        print(OKGREEN+"OK"+ENDC)
        index+=1

    if len(links) == 0:
        print(WARNING+"There are links on this page, but none of them are usefull."+ENDC)
        # Go back in history
        old_url = driver.current_url
        driver.back()
        new_url = driver.current_url
        # Page did not change even after going back? That's not good... End the program.
        if old_url == new_url:
            print(FAIL+"There's no page to go back to!"+ENDC)
            break
        else:
            # Index previous website once again
            url_to_index=new_url
            # Singalize that we're going back
            going_back = True
    else:
        for link in links:
            url_to_index=link

# End browser session
driver.quit()
