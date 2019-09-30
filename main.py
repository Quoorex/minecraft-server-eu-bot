import os
import time
import json

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from webdrivermanager import GeckoDriverManager

from util import get_lines


class Votebot():

    def __init__(self):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))

    def install_driver(self):
        gdd = GeckoDriverManager()
        gdd.download_and_install()

    def init_driver(self, headless):
        # Initialize a Firefox webdriver
        while True:
            try:
                options = Options()
                if headless == "True":
                    options.headless = True
                profile = webdriver.FirefoxProfile()
                profile.set_preference('dom.webdriver.enabled', False)
                driver = webdriver.Firefox(profile, options=options)
                break
            except WebDriverException:
                self.install_driver()
                continue  # Retry
        return driver

    def install_ext(self, driver):
        extension_dir = self.project_dir + "/browser/extensions/"

        extensions = [
            "{e58d3966-3d76-4cd9-8552-1582fbc800c1}.xpi",
            "uBlock0@raymondhill.net.xpi"
        ]

        for ext in extensions:
            driver.install_addon(extension_dir + ext)

    def vote(self, driver, username, vote_url):
        driver.get(vote_url)

        time.sleep(3)

        try:
            # Accept TOS
            submit_button = driver.find_element_by_xpath("/html/body/div[1]/div/div/div[2]/button[2]")
            submit_button.click()
        except NoSuchElementException:
            pass  # No TOS popup

        time.sleep(2)

        try:
            # We use .find_element_by_id here because we know the id
            text_input = driver.find_element_by_id("playername")

            # Then we'll fake typing into it
            text_input.send_keys(username)

            time.sleep(2)
        except NoSuchElementException:
            pass  # Users cannot recieve rewards for voting

        # Now we can grab the submit button and click it
        submit_button = driver.find_element_by_id("captcha")
        submit_button.click()

        time.sleep(4)

        try:
            # Try to solve a captcha with the browser extension Buster
            driver.switch_to.frame(driver.find_element_by_xpath('//*[@title="recaptcha challenge"]'))
            time.sleep(3)
            buster_button = driver.find_element_by_xpath('//*[@id="solver-button"]')
            buster_button.click()
        except NoSuchElementException:
            pass  # No captcha

        # TODO Optimize the url check
        while ("success" in driver.current_url or "fail" in driver.current_url) is False:
            time.sleep(0.5)

        if "success" in driver.current_url:
            print(f"Voted successfully for {username}")
        elif "fail" in driver.current_url:
            print(f"Couldn't vote for {username}")

        driver.close()

    def run(self, username, vote_url, headless):
        driver = self.init_driver(headless)
        self.install_ext(driver)
        while True:
            try:
                self.vote(driver, username, vote_url)
                break
            except UnexpectedAlertPresentException:
                # Captcha Error
                continue


if __name__ == "__main__":
    bot = Votebot()
    with open("config.json") as f:
        conf = json.load(f)

    usernames = get_lines(conf["username_file"])  # Users to get the voting reward for
    vote_urls = get_lines(conf["vote_url_file"])  # URL to the vote page of a server on minecraft-server.eu
    headless = conf["headless"]

    for user in usernames:
        for vote_url in vote_urls:
            bot.run(user, vote_url, headless)
