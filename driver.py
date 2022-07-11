from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
)

class Driver:

    def __init__(self, browser) -> None:
        self.browser = browser
        self.driver = None

    def web_driver_load(self):
        if self.browser.lower() == "chrome":
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--mute-audio")
            self.driver = webdriver.Chrome(options=chrome_options)
        elif self.browser.lower() == "firefox":
            self.driver = webdriver.Firefox()
        else:
            print("Browser not supported\n")

    def web_driver_quit(self):
        self.driver.quit()


    def wait_till_you_get(self, identifier, by, all=False, click_xpath="", visible_check=True):
        while True:
            try:
                elements = self.driver.find_elements(by, identifier)
                if not all:
                    if (not visible_check) or (
                        elements and elements[0].is_displayed() and elements[0].is_enabled()
                    ):
                        return elements[0]
                    else:
                        if click_xpath:
                            self.wait_till_you_get(click_xpath, By.XPATH).click()
                else:
                    return elements
            except NoSuchElementException:
                if click_xpath:
                    self.wait_till_you_get(click_xpath, By.XPATH).click()


    def wait_as_long_as(self, identifier, by):
        while True:
            try:
                self.driver.find_element(by, identifier)
            except (NoSuchElementException):
                break

    def google_login(self, google_creds):
        self.driver.get("https://accounts.google.com/servicelogin")
        self.wait_till_you_get("identifier", By.NAME).send_keys(
            google_creds["username"], Keys.RETURN
        )
        self.wait_till_you_get("password", By.NAME).send_keys(
            google_creds["password"], Keys.RETURN
        )
        self.wait_as_long_as("password", By.NAME)

    def get(self, url):
        self.driver.get(url)