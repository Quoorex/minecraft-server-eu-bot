import os
import time
import json
import random
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from webdrivermanager import GeckoDriverManager
from fake_useragent import UserAgent

from util import get_lines, out


# TODO Replace time.sleep() with proper Selenium waiting functions

class Votebot():

    def __init__(self):
        self.project_dir = os.path.abspath(os.path.dirname(__file__))
        with open("config.json") as f:
            self.conf = json.load(f)
        self.proxies = get_lines(self.conf["proxy"]["file"])
        self.headless = self.conf["headless"]

    def install_driver(self):
        gdd = GeckoDriverManager()
        gdd.download_and_install()

    def init_driver(self):
        # Initialize a Firefox webdriver
        while True:
            try:
                options = Options()
                if self.headless == "True":
                    options.headless = True
                profile = webdriver.FirefoxProfile()
                profile.set_preference('dom.webdriver.enabled', False)

                if self.conf["fake_useragent"] == "True":
                    ua = UserAgent().random
                    profile.set_preference("general.useragent.override", ua)

                p_conf = self.conf["proxy"]
                if p_conf["enabled"] == "True":
                    proxy = random.choice(self.proxies)
                    host, port = proxy.split(":")
                    p_type = p_conf["type"].lower()
                    if p_type == "https":
                        p_type = "ssl"
                    profile.set_preference("network.proxy.type", 1)
                    profile.set_preference(f"network.proxy.{p_type}", host)
                    profile.set_preference(f"network.proxy.{p_type}_port", int(port))

                profile.update_preferences()
                driver = webdriver.Firefox(profile, options=options)
                break
            except WebDriverException:
                self.install_driver()
                continue  # Retry
        return driver

    def install_ext(self, driver):
        extension_dir = os.path.join(self.project_dir, "browser/extensions/")

        extensions = [
            "{e58d3966-3d76-4cd9-8552-1582fbc800c1}.xpi",
            "uBlock0@raymondhill.net.xpi"
        ]

        for ext in extensions:
            driver.install_addon(os.path.join(extension_dir, ext))

    def vote(self, driver, username, vote_url):
        driver.get(vote_url)

        # time.sleep(5)  # Wait for the page to properly load

        try:
            # Accept TOS
            tos_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'qc-cmp-ui-content')))
            actions = ActionChains(driver)
            actions.move_to_element(tos_box).perform()
            tos_box.click()
            submit_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[2]/button[2]")))
            submit_button.click()

        except TimeoutException:
            pass  # No TOS popup

        time.sleep(2)

        try:
            # We use .find_element_by_id here because we know the id
            text_input = driver.find_element_by_id("playername")

            time.sleep(10)

            text_input.click()

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
        i = 0
        while True:
            if "success" in driver.current_url or "fail" in driver.current_url:
                current_url = driver.current_url
                break
            elif i == 5:
                out(f"Captcha failed for {username}")
                raise UnexpectedAlertPresentException
            i += 1
            time.sleep(1)

        if "success" in current_url:
            out(f"Voted successfully for {username}")
        elif "fail" in current_url:
            out(f"Couldn't vote for {username}")

        driver.close()

    def run(self, usernames, vote_urls):
        for vote_url in vote_urls:
            out(f"Voting for the url {vote_url}")
            for username in usernames:
                driver = self.init_driver()
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

    usernames = get_lines(bot.conf["username_file"])  # Users to get the voting reward for
    vote_urls = get_lines(bot.conf["vote_url_file"])  # URL to the vote page of a server on minecraft-server.eu

    bot.run(usernames, vote_urls)

    if bot.conf["use_timer"] == "True":
        while True:
            # calculate a randomized time for the next execution
            time_till_next_day = datetime.combine(
                    datetime.now().date() + timedelta(days=1), datetime.strptime("0000", "%H%M").time()
                ) - datetime.now()

            delay = time_till_next_day + timedelta(hours=random.randint(2, 23))
            out(f"Next execution in: {delay}")
            time.sleep(delay.seconds)
            bot.run(usernames, vote_urls)
