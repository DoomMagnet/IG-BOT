from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
import time
from utility_methods.utility_methods import *
import urllib.request
import os
import random

class InstaBot:

    def __init__(self, username=None, password=None):
        """"
        Creates an instance of InstaBot class.
        Args:
            username:str: The username of the user, if not specified, read from configuration.
            password:str: The password of the user, if not specified, read from configuration.
        Attributes:
            driver_path:str: Path to the chromedriver.exe
            driver:str: Instance of the Selenium Webdriver (chrome 72) 
            login_url:str: Url for logging into IG.
            nav_user_url:str: Url to go to a users homepage on IG.
            get_tag_url:str: Url to go to search for posts with a tag on IG.
            logged_in:bool: Boolean whether current user is logged in or not.
        """

        self.username = config['IG_AUTH']['USERNAME']
        self.password = config['IG_AUTH']['PASSWORD']

        self.login_url = config['IG_URLS']['LOGIN']
        self.nav_user_url = config['IG_URLS']['NAV_USER']
        self.get_tag_url = config['IG_URLS']['SEARCH_TAGS']
        self.suggested_url = config['IG_URLS']['SUGGESTED']
        self.explore_url = config['IG_URLS']['EXPLORE']

        self.driver = webdriver.Chrome(config['ENVIRONMENT']['CHROMEDRIVER_PATH'])

        self.logged_in = False


    def login(self):
        """
        Logs a user into Instagram via the web portal
        """

        self.driver.get(self.login_url)
        time.sleep(2)

        login_btn = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div[1]/div/form/div[4]/button/div') # login button xpath changes after text is entered, find first

        username_input = self.driver.find_element_by_name('username')
        password_input = self.driver.find_element_by_name('password')

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        login_btn.click()

        time.sleep(3)


    def search_tag(self, tag):
        """
        Naviagtes to a search for posts with a specific tag on IG.
        Args:
            tag:str: Tag to search for
        """

        self.driver.get(self.get_tag_url.format(tag))


    def nav_user(self, user):
        """
        Navigates to a users profile page
        Args:
            user:str: Username of the user to navigate to the profile page of
        """

        self.driver.get(self.nav_user_url.format(user))


    def follow_user(self, user):
        """
        Follows user(s)
        Args:
            user:str: Username of the user to follow
        """

        self.nav_user(user)

        follow_buttons = self.find_buttons('Follow')

        for btn in follow_buttons:
            btn.click()

    
    def unfollow_user(self, user):
        """
        Unfollows user(s)
        Args:
            user:str: Username of user to unfollow
        """

        self.nav_user(user)
        unfollow_btns = self.driver.find_element_by_xpath("//button[@class='_5f5mN    -fzfL     _6VtSN     yZn4P   ']").click()
        self.find_buttons('Unfollow')[0].click()
    

    def download_user_images(self, user):
        """
        Downloads all images from a users profile.
        """
    
        self.nav_user(user)

        img_srcs = []
        finished = False
        while not finished:

            finished = self.infinite_scroll() # scroll down

            img_srcs.extend([img.get_attribute('src') for img in self.driver.find_elements_by_class_name('FFVAD')]) # scrape srcs

        img_srcs = list(set(img_srcs)) # clean up duplicates

        for idx, src in enumerate(img_srcs):
            self.download_image(src, idx, user)
    

    def like_latest_posts(self, user, n_posts, like=True):
        """
        Likes a number of a users latest posts, specified by n_posts.
        Args:
            user:str: User whose posts to like or unlike
            n_posts:int: Number of most recent posts to like or unlike
            like:bool: If True, likes recent posts, else if False, unlikes recent posts
        TODO: Currently maxes out around 15.
        """

        action = 'Like' if like else 'Unlike'

        self.nav_user(user)
        posts = self.driver.find_element_by_class_name('g47SY ').text
        posts = int(posts.replace(',',''))
        if n_posts > posts:
            n_posts = posts

        imgs = []
        imgs.extend(self.driver.find_elements_by_class_name('_9AhH0'))
        for img in imgs[:n_posts]:
            img.click() 
            time.sleep(1) 
            try:
                self.driver.find_element_by_xpath("//*[@aria-label='{}']".format(action)).click()
            except Exception as e:
                print(e)

            #self.comment_post('beep boop testing bot')
            time.sleep(1)
            close = self.driver.find_element_by_class_name('_8-yf5 ')
            actions = ActionChains(self.driver)
            actions.move_to_element(close).click().perform()

    def comment_post(self, text, n_posts, chance=0.6):
        """
        #Comments on a post that is in modal form
        """
        imgs = []
        imgs.extend(self.driver.find_elements_by_class_name('_9AhH0'))
        for img  in imgs[:n_posts]:
            img.click()
            time.sleep(2)
            try:
                if random.random() > chance:
                    commentArea = self.driver.find_element_by_class_name('Ypffh')
                    commentArea.click()
                    commentArea = self.driver.find_element_by_class_name('Ypffh')
                    commentArea.send_keys(text + Keys.RETURN)
            except Exception as e:
                print(e)

            time.sleep(1)
            close = self.driver.find_element_by_class_name('_8-yf5 ')
            actions = ActionChains(self.driver)
            actions.move_to_element(close).click().perform()

    def follow_suggested(self, num=15):
        self.driver.get(self.suggested_url)
        self.infinite_scroll()
        i = 1
        time.sleep(1)
        follow_buttons = self.find_buttons('Follow')
        while i != num+1:
            user = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div[2]/div/div/div['+str(i)+']')
            try:
                suggested_why = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div[2]/div/div/div['+str(i)+']/div[2]/div[3]/div').text
            except NoSuchElementException:
                suggested_why = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div[2]/div/div/div['+str(i)+']/div[2]/div[2]/div').text
            else:
                follow = follow_buttons[i]
                actions = ActionChains(self.driver)
                actions.move_to_element(follow).click().perform()
            i += 1
            time.sleep(random.uniform(0.3,1.5))

    def unfollow_many(self, num=5):
        self.driver.get(self.nav_user_url.format('cheap4lifespotify'))
        self.find_buttons(' following')[0].click()
        time.sleep(2)

        follow_buttons = self.driver.find_elements_by_xpath('//button[@class=\'sqdOP  L3NKy    _8A5w5    \']')
        for button in follow_buttons[:num]:
            button.click()
            self.driver.find_element_by_xpath('//button[@class=\'aOOlW -Cab_   \']').click()

    def download_image(self, src, image_filename, folder):
        """
        Creates a folder named after a user to to store the image, then downloads the image to the folder.
        """
        folder_path = './userImages/{}'.format(folder)
        os.makedirs(folder_path, exist_ok=True)

        img_filename = 'image_{}.jpg'.format(image_filename)
        folder = './userImages/' + folder
        urllib.request.urlretrieve(src, '{}/{}'.format(folder, img_filename))


    def infinite_scroll(self):
        """
        Scrolls to the bottom of a users page to load all of their media
        Returns:
            bool: True if the bottom of the page has been reached, else false
        """

        SCROLL_PAUSE_TIME = 2
        Done = False
        while Done == False:
            self.last_height = self.driver.execute_script("return document.body.scrollHeight")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(SCROLL_PAUSE_TIME)

            self.new_height = self.driver.execute_script("return document.body.scrollHeight")


            if self.new_height == self.last_height:
                Done = True
                return True


    def find_buttons(self, button_text):
        """
        Finds buttons for following and unfollowing users by filtering follow elements for buttons. Defaults to finding follow buttons.
        Args:
            button_text: Text that the desired button(s) has 
        """

        buttons = self.driver.find_elements_by_xpath("//*[text()='{}']".format(button_text))

        return buttons


if __name__ == '__main__':

    config_file_path = 'config.ini' 
    config = init_config(config_file_path)

    bot = InstaBot()
    bot.login()

    while True:
        time_sec = random.randint(3650,4500)
        bot.follow_suggested()
        sentence = "Upgrade your spotify account to premium forever for just $5! Warranty included. DM for details!"
        bot.driver.get(bot.explore_url)
        time.sleep(2)
        try:
            bot.comment_post(sentence,5,0.2)
        except ElementClickInterceptedException as e:
            pass
        time.sleep(time_sec)
    
