from selenium.webdriver.common.by import By
from driver import Driver
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


def comment_in_shorts(driver, url, comment, log):
    driver.get(url)
    channel = ""
    try:
        channel = (
            driver.wait_till_you_get("channel-name", By.ID)
            .find_element(By.CLASS_NAME, "yt-formatted-string")
            .text
        )
    except:
        pass
    driver.wait_till_you_get("comments-button", By.ID).click()
    driver.wait_till_you_get("placeholder-area", By.ID).click()
    driver.wait_till_you_get("contenteditable-root", By.ID).send_keys(comment)
    driver.wait_till_you_get("submit-button", By.ID).click()
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


def comment_in_video(driver, url, comment, log):
    driver.get(url)
    channel = ""
    try:
        channel = (
            driver.wait_till_you_get("channel-name", By.ID)
            .find_element(By.CLASS_NAME, "yt-formatted-string")
            .text
        )
    except:
        pass
    driver.wait_till_you_get("comment-teaser", By.ID).click()
    driver.wait_till_you_get("placeholder-area", By.ID).click()
    driver.wait_till_you_get("contenteditable-root", By.ID).send_keys(comment)
    driver.wait_till_you_get("submit-button", By.ID).click()
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


def target_top_daily(driver, top_daily_config, comment_config):
    search_url = (
        "https://www.youtube.com/results?search_query={TERM}&sp=CAMSBAgCEAE%253D"
    )
    count = top_daily_config["count"]
    search_terms = top_daily_config["terms"]

    for search_term in search_terms:
        search_term = re.sub(r"[^A-Za-z0-9 ]+", "", search_term).lower()
        search_term = search_term.replace(" ", "+")
        driver.get(search_url.format(TERM=search_term))

        video_elems = driver.wait_till_you_get(
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
                    driver=driver,
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
                    driver=driver,
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

    driver = Driver(browser)
    
    try:
        driver.web_driver_load()
        driver.google_login(google_creds)

        target_top_daily(driver, top_daily_config, comment_config)
    finally:
        sent_logs.to_csv(LOG_FILE, index=False)
        driver.web_driver_quit()
        
    print("Done n Dusted. Now we wait.")
