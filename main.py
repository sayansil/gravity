from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
)
import time
import re
import os
import random
import json
import pandas as pd
from datetime import datetime

CONFIG_FILE = "config.json"

# Use local config file if exists
if os.path.exists("local-" + CONFIG_FILE):
    CONFIG_FILE = "local-" + CONFIG_FILE

LOG_FILE = "sent.csv"

sent_logs = None

driver = None
inaction_delay = 0

# Create DB during the first run
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w"):
        pass


def append_sent_logs(log):
    log_list = [
        log["url"],
        log["channel"],
        log["ts"],
        log["type"],
        log["comment"],
        log["meta"],
    ]
    sent_logs.loc[len(sent_logs.index)] = log_list


def spam_check(url):
    return url in sent_logs["url"]

def relevance_check(url):
    # TODO
    return True


def wait_till_you_get(identifier, by, all=False, click_xpath="", visible_check=True):
    while True:
        try:
            elements = driver.find_elements(by, identifier)
            if not all:
                if (not visible_check) or (
                    elements and elements[0].is_displayed() and elements[0].is_enabled()
                ):
                    return elements[0]
                else:
                    if click_xpath:
                        wait_till_you_get(click_xpath, By.XPATH).click()
            else:
                return elements
        except NoSuchElementException:
            if click_xpath:
                wait_till_you_get(click_xpath, By.XPATH).click()


def wait_as_long_as(identifier, by):
    while True:
        try:
            driver.find_element(by, identifier)
        except (NoSuchElementException):
            break


def send_keys_when_you_can(element, key):
    while True:
        try:
            element.send_keys(key)
            break
        except ElementNotInteractableException:
            pass


def web_driver_load(browser):
    global driver
    if browser.lower() == "chrome":
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--mute-audio")
        driver = webdriver.Chrome(options=chrome_options)
    elif browser.lower() == "firefox":
        driver = webdriver.Firefox()
    else:
        print("Browser not supported\n")


def web_driver_quit():
    driver.quit()


def google_login(google_creds):
    driver.get("https://accounts.google.com/servicelogin")
    wait_till_you_get("identifier", By.NAME).send_keys(
        google_creds["username"], Keys.RETURN
    )
    wait_till_you_get("password", By.NAME).send_keys(
        google_creds["password"], Keys.RETURN
    )
    wait_as_long_as("password", By.NAME)


def comment_in_shorts(url, comment, log):
    driver.get(url)
    channel = ""
    try:
        channel = (
            wait_till_you_get("channel-name", By.ID)
            .find_element(By.CLASS_NAME, "yt-formatted-string")
            .text
        )
    except:
        pass
    wait_till_you_get("comments-button", By.ID).click()
    wait_till_you_get("placeholder-area", By.ID).click()
    wait_till_you_get("contenteditable-root", By.ID).send_keys(comment)
    wait_till_you_get("submit-button", By.ID).click()
    append_sent_logs(
        {
            "url": url,
            "channel": channel,
            "ts": datetime.now(),
            "type": log["type"],
            "comment": comment,
            "meta": log["meta"],
        }
    )
    time.sleep(inaction_delay)


def comment_in_video(url, comment, log):
    driver.get(url)
    channel = ""
    try:
        channel = (
            wait_till_you_get("channel-name", By.ID)
            .find_element(By.CLASS_NAME, "yt-formatted-string")
            .text
        )
    except:
        pass
    wait_till_you_get("comment-teaser", By.ID).click()
    wait_till_you_get("placeholder-area", By.ID).click()
    wait_till_you_get("contenteditable-root", By.ID).send_keys(comment)
    wait_till_you_get("submit-button", By.ID).click()
    append_sent_logs(
        {
            "url": url,
            "channel": channel,
            "ts": datetime.now(),
            "type": log["type"],
            "comment": comment,
            "meta": log["meta"],
        }
    )
    time.sleep(inaction_delay)


def generate_comment(comment_config):
    syntax = random.choice(comment_config["syntax"])
    link = random.choice(comment_config["links"])
    return syntax.format(LINK=link)


def target_top_daily(top_daily_config, comment_config):
    search_url = (
        "https://www.youtube.com/results?search_query={TERM}&sp=CAMSBAgCEAE%253D"
    )
    count = top_daily_config["count"]
    search_terms = top_daily_config["terms"]

    for search_term in search_terms:
        search_term = re.sub(r"[^A-Za-z0-9 ]+", "", search_term).lower()
        search_term = search_term.replace(" ", "+")
        driver.get(search_url.format(TERM=search_term))

        video_elems = wait_till_you_get(
            "title-and-badge", By.CLASS_NAME, all=True, visible_check=False
        )[:count]
        youtube_urls = {"video": [], "shorts": []}

        for video in video_elems:
            try:
                url = video.find_element(
                    By.CLASS_NAME, "yt-simple-endpoint"
                ).get_attribute("href")
                if url:
                    if "/shorts/" in url:
                        youtube_urls["shorts"].append(url)
                    else:
                        youtube_urls["video"].append(url)
            except Exception:
                continue

        youtube_urls["shorts"] = list(set(youtube_urls["shorts"]))
        youtube_urls["video"] = list(set(youtube_urls["video"]))

        for short_url in youtube_urls["shorts"]:
            if relevance_check(short_url) and not spam_check(short_url):
                comment_in_shorts(
                    url=short_url,
                    comment=generate_comment(comment_config),
                    log={
                        "type": "top_daily",
                        "meta": json.dumps({"keyword": search_term}),
                    },
                )
        for video_url in youtube_urls["video"]:
            if relevance_check(short_url) and not spam_check(short_url):
                comment_in_video(
                    url=video_url,
                    comment=generate_comment(comment_config),
                    log={
                        "type": "top_daily",
                        "meta": json.dumps({"keyword": search_term}),
                    },
                )


if __name__ == "__main__":
    browser = "Chrome"
    google_creds = {}
    top_daily_config = {}
    comment_config = {}

    try:
        with open(CONFIG_FILE) as config_file:
            configs = json.load(config_file)
            if "BROWSER" in configs:
                browser = configs["BROWSER"]
            if "INACTION_DELAY" in configs:
                inaction_delay = configs["INACTION_DELAY"]
            if "TOP-DAILY" in configs:
                top_daily_config["count"] = configs["TOP-DAILY"]["COUNT"]
                top_daily_config["terms"] = configs["TOP-DAILY"]["SEARCH-TERMS"]
            if "COMMENT" in configs:
                comment_config["syntax"] = configs["COMMENT"]["SYNTAX"]
                comment_config["links"] = configs["COMMENT"]["LINKS"]
            if "GOOGLE_USERNAME" in configs and "GOOGLE_PASSWORD" in configs:
                google_creds["username"] = configs["GOOGLE_USERNAME"]
                google_creds["password"] = configs["GOOGLE_PASSWORD"]
    except:
        pass

    sent_logs = pd.read_csv(LOG_FILE)
    if sent_logs.empty:
        sent_logs = pd.DataFrame(
            columns=["url", "channel", "ts", "type", "comment", "meta"]
        )

    try:
        web_driver_load(browser)
        google_login(google_creds)

        target_top_daily(top_daily_config, comment_config)
    finally:
        web_driver_quit()

    sent_logs.to_csv(LOG_FILE, index=False)
    print("Done n Dusted. Now we wait.")
