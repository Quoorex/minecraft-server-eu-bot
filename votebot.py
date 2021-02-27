import time
import platform
import random
from datetime import datetime, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from webdrivermanager import GeckoDriverManager
from fake_useragent import UserAgent
import yaml
import sys
import subprocess

from util import get_lines, out

# TODO Replace time.sleep() with proper Selenium waiting functions


class bcolors:
    with open("config.yaml") as f:
        conf = yaml.safe_load(f)
        if conf['use_colors']:
            HEADER = '\033[95m'
            OKBLUE = '\033[94m'
            OKCYAN = '\033[96m'
            OKGREEN = '\033[92m'
            WARNING = '\033[93m'
            FAIL = '\033[91m'
            ENDC = '\033[0m'
            BOLD = '\033[1m'
            UNDERLINE = '\033[4m'
        else:
            HEADER = ''
            OKBLUE = ''
            OKCYAN = ''
            OKGREEN = ''
            WARNING = ''
            FAIL = ''
            ENDC = ''
            BOLD = ''
            UNDERLINE = ''


class Votebot():

    def __init__(self):
        self.project_dir = Path.absolute(Path(__file__).parent)
        self.host_os = platform.system()
        with open("config.yaml") as f:
            self.conf = yaml.safe_load(f)
        self.proxies = get_lines(self.conf["proxy"]["file"])
        self.headless = self.conf["headless"]

    def install_driver(self):
        gdd = GeckoDriverManager()
        gdd.download_and_install()

    def set_viewport_size(self, driver, width, height):
        window_size = driver.execute_script("""
            return [window.outerWidth - window.innerWidth + arguments[0],
            window.outerHeight - window.innerHeight + arguments[1]];
            """, width, height)
        driver.set_window_size(*window_size)

    def init_driver(self):
        # Initialize a webdriver
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
                    elif p_type == "socks":
                        profile.set_preference(
                            "network.proxy.socks_version", p_conf["socks_version"])
                    elif p_type == "http":
                        # Allow the usage of the http proxy for https requests
                        profile.set_preference(
                            "network.proxy.share_proxy_settings", True)
                    profile.set_preference("network.proxy.type", 1)
                    profile.set_preference(f"network.proxy.{p_type}", host)
                    profile.set_preference(
                        f"network.proxy.{p_type}_port", int(port))

                profile.update_preferences()

                driver_filename_extension = ""
                if (self.host_os == "Linux" or self.host_os == "Darwin"):  # Linux or MacOS
                    driver_folder = "macos" if self.host_os == "Darwin" else "linux"
                elif self.host_os == "Windows":
                    driver_folder = "windows"
                    driver_filename_extension = ".exe"
                driver_path = str(Path.joinpath(
                    self.project_dir, f"browser/driver/{driver_folder}/geckodriver{driver_filename_extension}"))

                driver = webdriver.Firefox(
                    profile, options=options, executable_path=driver_path)
                break
            except WebDriverException:
                self.install_driver()
                continue  # Retry
        return driver

    def install_ext(self, driver):
        extension_dir = Path.joinpath(self.project_dir, "browser/extensions/")

        extensions = [
            "{e58d3966-3d76-4cd9-8552-1582fbc800c1}.xpi",
            "uBlock0@raymondhill.net.xpi"
        ]

        for ext in extensions:
            # Path has to be converted to a string because a path object won't work here
            driver.install_addon(str(Path.joinpath(extension_dir, ext)))

    def try_captcha(self, driver):
        try:
            driver.switch_to.default_content()
            time.sleep(1)
            driver.switch_to.frame(driver.find_element_by_xpath(
                "//*[@title='recaptcha challenge']"))
        except NoSuchElementException:
            # hCaptcha ?
            try:
                driver.switch_to.default_content()
                time.sleep(1)
                driver.switch_to.frame(driver.find_element_by_xpath(
                    "//*[@title='Main content of the hCaptcha challenge']"))
            except NoSuchElementException:
                return

            try:
                driver.find_element_by_xpath(
                    '//div[@class="border"]').click()
            except NoSuchElementException:
                pass

            try:
                driver.find_element_by_xpath(
                    '//div[@class="button submit-button"]').click()
            except NoSuchElementException:
                pass

        time.sleep(2)

        try:
            driver.find_element_by_xpath(
                '//*[@id="solver-button"]').click()
            return
        except (NoSuchElementException, ElementNotInteractableException):
            pass

        time.sleep(3)

        try:
            outside_shadow = driver.find_element_by_xpath(
                "//div[@class='button-holder help-button-holder']")

            shadow_root = driver.execute_script(
                'return arguments[0].shadowRoot', outside_shadow)

            if shadow_root is not None:
                shadow_root.find_element_by_xpath(
                    '//*[@id="solver-button"]').click()
        except NoSuchElementException:
            pass

    def try_open_captcha(self, driver):
        try:
            # Try to solve a captcha with the browser extension Buster
            driver.switch_to.frame(driver.find_element_by_xpath(
                "//div[contains(@class,'g-recaptcha')]/div/div/iframe"))
            checkbox = driver.find_element_by_xpath(
                '//span[contains(@class,"recaptcha-checkbox")]')
            checkbox.click()
            time.sleep(0.1)
            checkbox.click()

            return
        except NoSuchElementException:
            pass

        try:
            # Try to solve a captcha with the browser extension Buster
            driver.switch_to.frame(driver.find_element_by_xpath(
                "//div[contains(@class,'h-recaptcha')]/iframe"))
            checkbox = driver.find_element_by_id("checkbox")
            checkbox.click()
            time.sleep(0.1)
            checkbox.click()

            return
        except NoSuchElementException:
            pass

    def vote(self, driver, username, vote_url):
        # TODO set viewport depending on whether a mobile or desktop useragent is used
        self.set_viewport_size(driver, 1920, 1080)
        driver.get(vote_url)

        time.sleep(1)

        self.try_open_captcha(driver)

        time.sleep(0.5)

        self.try_captcha(driver)

        time.sleep(5)

        driver.switch_to.default_content()

        try:
            # We use .find_element_by_id here because we know the id
            if 'minecraft-server-list.com' in vote_url:
                text_input = driver.find_element_by_id(
                    "ignn")
                submit_button = driver.find_element_by_name("button")
            elif 'mc-servers.com' in vote_url:
                try:
                    driver.find_element_by_xpath(
                        '//a[@class="cc-btn cc-dismiss"]').click()
                except Exception:
                    pass
                text_input = driver.find_element_by_name(
                    "username")
                possible_submits = driver.find_elements_by_xpath(
                    "//button[@type='submit']")
                for button in possible_submits:
                    if button.text == 'Vote':
                        submit_button = button
                        break
                if 'submit_button' not in locals():
                    raise NoSuchElementException
            elif 'topg.org' in vote_url:
                text_input = driver.find_element_by_id('game_user')
                submit_button = driver.find_element_by_name("submit")
            elif 'bestservers.com' in vote_url:
                text_input = driver.find_element_by_name('username')
                submit_button = driver.find_element_by_name("submit")
            elif 'topminecraftservers.org' in vote_url:
                text_input = driver.find_element_by_name('mc_username')
                submit_button = driver.find_element_by_name("voteSubmit")
            elif 'minecraft-mp.com' in vote_url:
                try:
                    driver.find_element_by_id('cookiescript_accept').click()
                except NoSuchElementException:
                    pass
                driver.find_element_by_name('accept').click()
                text_input = driver.find_element_by_name('nickname')
                submit_button = driver.find_element_by_id("voteBtn")
            elif 'minecraft-server.net' in vote_url:
                text_input = driver.find_element_by_id('mc_user')
                driver.find_element_by_xpath("//label[@for='rate-10']").click()
                submit_button = driver.find_element_by_xpath(
                    "//input[@value='Confirm Vote']")
            elif 'minecraftservers.org' in vote_url:
                text_input = driver.find_element_by_name('username')
                submit_button = driver.find_element_by_xpath(
                    "//button[@class='button vote submit']")

            text_input.click()

            time.sleep(0.5)

            # Then we'll fake typing into it
            text_input.send_keys(username)

        except NoSuchElementException:
            out(f"{bcolors.FAIL}Failed to find text or vote button{bcolors.ENDC} (Could be because the page is blocking additional votes)")
            return  # Users cannot recieve rewards for voting

        time.sleep(4)

        self.try_open_captcha(driver)

        time.sleep(0.5)

        self.try_captcha(driver)

        time.sleep(2)

        try:
            driver.switch_to.default_content()
            submit_button.click()
        except NoSuchElementException:
            out(f"{bcolors.FAIL}Failed to find vote button{bcolors.ENDC}")
            return

        time.sleep(2)

        self.try_captcha(driver)

        # TODO Optimize the url check
        while True:
            if 'minecraft-server-list.com' in vote_url:
                votepasses = driver.find_elements_by_xpath(
                    "//div[@id='voteerror']/font[@color='green']")
                votefails = driver.find_elements_by_xpath(
                    "//div[@id='voteerror']/font[@color='red']")
                if len(votepasses) > 0:
                    success = True
                    break
                elif len(votefails) > 0:
                    success = False
                    break
            elif 'topg.org' in vote_url:
                if driver.current_url == 'https://topg.org/Minecraft':
                    success = True
                    break
                elif len(driver.find_elements_by_xpath("//p[@class='alert alert-warning centered']")) > 0:
                    success = False
                    break
            elif 'bestservers.com' in vote_url:
                if len(driver.find_elements_by_xpath("//div[@class='ui success message']")) > 0:
                    success = True
                    break
                elif len(driver.find_elements_by_xpath("//div[@class='ui error message']")) > 0:
                    success = False
                    break
            elif 'topminecraftservers.org' in vote_url:
                votedalready = driver.find_elements_by_xpath(
                    "//button[@disabled='disabled']")
                for button in votedalready:
                    if button.text == "You've already voted today!":
                        success = True
                        break
                success = False
                break
            elif 'minecraft-mp.com' in vote_url:
                if 'confirm' in driver.current_url:
                    success = True
                    break
                elif 'error' in driver.current_url:
                    success = False
                    break
            elif 'minecraft-server.net' in vote_url:
                if driver.current_url == 'https://minecraft-server.net/':
                    if len(driver.find_elements_by_xpath("//div[@class='alert alert-danger mt-2']")) > 0:
                        success = False
                    else:
                        success = True
                    break
            elif 'mc-servers.com' in vote_url:
                possible_errors = driver.find_elements_by_xpath(
                    "//p")
                for error in possible_errors:
                    if error.text == 'You already voted today':
                        success = False
                        break
                if len(driver.find_elements_by_xpath(
                        '//span[@class="left badge green white-text"]')) > 0:
                    success = True
                    break
            elif 'minecraftservers.org' in vote_url:
                if driver.current_url == 'https://minecraftservers.org/server/47497' and len(driver.find_elements_by_xpath('//div[@class="flash"]')) > 0:
                    success = True
                    break
                if len(driver.find_elements_by_xpath('//div[@class="error-message"]')) > 0:
                    success = False
                    break
                if len(driver.find_elements_by_xpath('//span[@class="validation-error"]')) > 0:
                    # captcha was failed
                    break

            else:
                out(f"{bcolors.FAIL}Unsure if the vote worked. Check yourself{bcolors.ENDC}")
                success = False
                if len(input('Press enter to retry, or type anything and then press enter to stop ')) > 0:
                    break

            raise UnexpectedAlertPresentException

        if success:
            out(f"{bcolors.OKGREEN}Voted successfully!{bcolors.ENDC}")
        else:
            out(f"{bcolors.FAIL}Vote went through, but was unsuccessful!{bcolors.ENDC} (Page is blocking additional votes)")

        return success

    def run(self, usernames, vote_urls, captcha_retries, num_users):

        random.shuffle(usernames)
        random.shuffle(vote_urls)

        sum_votes = 0
        for username in usernames[0:num_users]:
            out(f"Voting for {bcolors.OKCYAN}{username}{bcolors.ENDC}")
            votes = 0
            for vote_url in vote_urls:
                out(f"Trying to vote at {vote_url}")
                driver = self.init_driver()
                self.install_ext(driver)
                for _ in range(captcha_retries):
                    try:
                        votes += 1 if self.vote(driver,
                                                username, vote_url) else 0
                        break
                    except (UnexpectedAlertPresentException, ElementClickInterceptedException):
                        # Captcha Error
                        if _ < captcha_retries - 1:
                            out(f"{bcolors.WARNING}Retrying vote{bcolors.ENDC}")
                        else:
                            out(f"{bcolors.HEADER}Failed to vote{bcolors.ENDC}")
                        continue
                    except KeyboardInterrupt:
                        break

                driver.close()

            out(f"Voted {bcolors.WARNING}{votes}{bcolors.ENDC} times for {bcolors.OKCYAN}{username}{bcolors.ENDC}")
            sum_votes += votes
        out(
            f"Voted a total of {bcolors.WARNING}{sum_votes}{bcolors.ENDC} times for {bcolors.HEADER}{len(usernames[0:num_users])}{bcolors.ENDC} users")


if __name__ == "__main__":
    bot = Votebot()

    # Users to get the voting reward for
    usernames = get_lines(bot.conf["username_file"])
    # URL to the vote page of a server on minecraft-server.eu
    vote_urls = get_lines(bot.conf["vote_url_file"])

    captcha_tries = bot.conf["captcha_tries"]

    if len(sys.argv) >= 3 and sys.argv[2] == "True" or bot.conf["delay"] == 0:
        try:
            bot.run(usernames, vote_urls, captcha_tries,
                    bot.conf["users_per_round"])
        except WebDriverException:
            out(f"{bcolors.FAIL}Probably not connected to the internet!{bcolors.ENDC}")

        delay = timedelta(hours=bot.conf["timer_min"]) + \
            timedelta(seconds=random.randint(
                0, 60 * 60 * (bot.conf["timer_max"] - bot.conf["timer_min"])))
        out(f"Next execution in: {bcolors.WARNING}{delay}{bcolors.ENDC}")
        time.sleep(1)
        p = subprocess.Popen(f"sleep {delay.seconds} && python votebot.py True",
                             stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
    else:
        delay = timedelta(hours=bot.conf["delay"])
        out(f"Beginning execution in: {bcolors.WARNING}{delay}{bcolors.ENDC}")
        time.sleep(1)
        p = subprocess.Popen(f"sleep {delay.seconds} && python votebot.py True",
                             stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)

    out('')
    out("Now running in the background.")
    out(
        f"Run {bcolors.FAIL}kill -9 {p.pid}{bcolors.ENDC} to stop.")
    out(
        f"Run {bcolors.WARNING}cat bot.log{bcolors.ENDC} to see the logs")
    out("Note: the Process ID changes every time it executes. Check the log for the updated command if you want to stop the bot from running.")
