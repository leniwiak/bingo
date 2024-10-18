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

def exists(link):
    try:
        cur.execute("SELECT link FROM searches WHERE link=?", (link,))
        searches_len = len(cur.fetchall())
        cur.execute("SELECT link FROM useless_searches WHERE link=?", (link,))
        useless_len = len(cur.fetchall())
        return (searches_len != 0 or useless_len != 0)
    except Exception as err:
        print(FAIL+"Database task failed. Cannot check existance because of an error: "+type(err).__name__+ENDC)
        time.sleep(1)
        exists(link)

def save(title, desc, language, link):
    print(OKGREEN+"---")
    print("title: "+title)
    print("desc:  "+desc)
    print("lang:  "+language)
    print("link:  "+link)
    print("---"+ENDC)
    now = datetime.datetime.utcnow()
    date = int(str(now.year)+str(now.month)+str(now.day))

    try:
        cur.execute("INSERT INTO 'searches' (title, desc, language, link, date) VALUES(?, ?, ?, ?, ?)", (title, desc, language, link, date))
        con.commit()
        return
    except Exception as err:
        print(FAIL+"Database task failed. Cannot save because of an error: "+type(err).__name__+ENDC)
        print(err)
        time.sleep(1)
        save(title, desc, language, link)

def save_useless_result(link):
    print(FAIL+"---")
    print("link:  "+link)
    print("---"+ENDC)

    try:
        cur.execute("INSERT INTO 'useless_searches' (link) VALUES(?)", (link,))
        con.commit()
        return
    except Exception as err:
        print(FAIL+"Database task failed. Cannot save useless result because of an error: "+type(err).__name__+ENDC)
        print(err)
        time.sleep(1)
        save_useless_result(link)

first_iter = True

def goback():
    print("---")
    print("Going back...")
    global first_iter
    global url_to_index
    global history
    global going_back

    history_length = len(history)
    print("There are "+OKBLUE+str(history_length)+ENDC+" elements in history.")

    if history_length <= 1:
        print(FAIL+"This is the end of session history. No page to go back to!"+ENDC)
        exit(1)

    going_from = history[-1]
    history.pop()
    going_to = history[-1]

    print("Old URL: "+going_from)
    print("New URL: "+going_to)

    first_iter = True
    going_back = True
    url_to_index=going_to

    print("---")

# Create a database for searches if it doesn't exist yet
cur.execute("CREATE TABLE IF NOT EXISTS 'searches' ('id' integer primary key autoincrement unique not null, 'title' text not null, 'desc' text, 'link' text unique not null, 'language' text, 'date' integer not null, 'like' integer not null default 0, 'dislike' integer not null default 0)")
# Create a database for link that aren't usable in our search engine
cur.execute("CREATE TABLE IF NOT EXISTS 'useless_searches' ('id' integer primary key autoincrement unique not null, 'link' text unique not null)")

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

# History of visited sites in session
going_back = False
history = []

if keep_domain:
    print("Keeping domain:",init_website)

# Go to specified URL
while True:
    print(OKBLUE+url_to_index+ENDC)

    if not going_back:
        history.append(url_to_index)

    try:
        driver.get(url_to_index)
    except TimeoutException:
        print(WARNING+"Timeout occured! Waiting 5 seconds..."+ENDC)
        time.sleep(5)
        going_back = True
        continue
    except Exception as err:
        print(FAIL+"Driver error occured: ("+type(err).__name__+")"+ENDC)
        # Go back in history
        goback()

    #driver.implicitly_wait(0.25)

    # Get title and description
    title = ""
    try:
        title = driver.title
        # Strip trailing newlines
        title = title.strip()
    except Exception as err:
        print(WARNING+"Failed to get contents of <title>: "+type(err).__name__+ENDC)

    if title == None:
        title = ""


    language = ""
    try:
        language = driver.find_element(By.TAG_NAME, "html").get_attribute("lang").strip()
    except Exception as err:
        print(WARNING+"Failed to get contents of <html lang=\"\">: "+type(err).__name__+ENDC)

    desc = ""
    if desc == "":
        meta_description = ""
        try:
            meta_description=driver.find_element(By.XPATH,"//meta[@name='description']").get_attribute("content").strip()
        except Exception as err:
            print(WARNING+"Failed to get contents of <meta name=\"description\" content=\"\">: "+type(err).__name__+ENDC)

    if desc == "":
        paragraph_tag = ""
        try:
            paragraph_tag = driver.find_element(By.TAG_NAME, "p").text.strip()
        except Exception as err:
            print(WARNING+"Failed to get contents of <p>: "+type(err).__name__+ENDC)

    if desc == "":
        header_tag = ""
        try:
            header_tag = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except Exception as err:
            print(WARNING+"Failed to get contents of <h1>: "+type(err).__name__+ENDC)

    # Save current website to the database
    # Skip saving (and do not print any error) if the script just started and website is already in db.
    if first_iter and exists(link=url_to_index.strip("/")):
        print("This site has been already added to the database but the script just started or went back from some weird page. It's probably okay to just skip saving and not bother.")
    else:
        save(title=title, desc=desc, language=language, link=url_to_index)

    if first_iter:
        first_iter = False
    if going_back:
        going_back = False

    # Get list of links
    try:
        links = driver.find_elements(By.TAG_NAME, "a")
    except:
        print(WARNING+"No links found on this page"+ENDC)
        # Go back in history
        goback()

    # Modify 'links' to only contain values of 'href' attributes
    index = 0
    while index < len(links):
        try:
            # Always make text lowercase and remove all useless slashes
            href = links[index].get_attribute("href").lower().strip("/")
            links[index] = href
            index+=1
        except:
            print("Failed to get 'href' attribute")
            links.pop(index)

    # Throw away hyperlinks that are useless at the first glance
    index = 0
    while index < len(links):
        if not links:
            break

        link = links[index].strip('/')

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

        if link == "":
            print(link, FAIL+"Link is empty!"+ENDC)
            links.pop(index)
            continue

        if "javascript:" in link:
            print(link, FAIL+"Contains 'javascript:' text!"+ENDC)
            links.pop(index)
            continue

        if exists(link=link.strip("/")):
            print(link, WARNING+"Already indexed!"+ENDC)
            links.pop(index)
            continue

        if keep_domain and init_website not in urlparse(link).netloc:
            print(link, WARNING+"Rejected by 'keep_domain' policy!"+ENDC)
            links.pop(index)
            continue
        index+=1

    # Remove duplicated values in list by converting it to a set and then going back to the list
    links = list(set(links))

    # Check if the website behind the link is accessible.
    # For example, a link may point to non-existing site, a file or something even worse
    # This is obviously bad. Save those useless links to the database using SAVE_USELESS_RESULT()
    index = 0
    while index < len(links):
        if not links:
            break

        link = links[index].strip('/')

        try:
            response = requests.head(link, timeout=10, allow_redirects=True)
            status_code = int(response.status_code)
            content_type = response.headers['content-type']
        except Exception as err:
                aaa=type(err).__name__
                if aaa == "ReadTimeout":
                    print(link, WARNING+"Got timeout error. Waiting 5 seconds..."+ENDC)
                    time.sleep(5)
                    continue
                else:
                    print(link, FAIL+"Failed to connect ("+aaa+")"+ENDC)
                    save_useless_result(link=link)
                    links.pop(index)
                    continue

        if "text/" not in content_type:
            print(link, FAIL+"Wrong content-type! ("+str(content_type)+")"+ENDC)
            save_useless_result(link=link)
            links.pop(index)
            continue
        elif status_code not in good_status_codes:
            print(link, FAIL+"Wrong status code! ("+str(status_code)+")"+ENDC)
            save_useless_result(link=link)
            links.pop(index)
            continue
        else:
            print(link, OKGREEN+"OK"+ENDC)
            index+=1
            continue

    if not links:
        print(WARNING+"There are links on this page, but none of them are usefull."+ENDC)
        # Go back in history
        goback()
    else:
        if not no_follow:
            for link in links:
                url_to_index=link.strip("/")
        else:
            print("Not following any link. That's it")
            exit(0)

# End browser session
driver.quit()
