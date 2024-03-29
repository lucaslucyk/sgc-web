from selenium import webdriver
from apps.scg_app.models import Clase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.conf import settings
import time

class BrowserConfigure:
    """ Setup and close browser definitions """
    
    def setUp(self):
        self.browser = webdriver.Firefox(
            executable_path=r'browser_tests\geckodriver.exe')

    def tearDown(self):
        self.browser.close()


class TestFirefox(BrowserConfigure, StaticLiveServerTestCase):
    """ All firefox browser tests. """

    def test_index(self):
        self.browser.get(self.live_server_url)

        time.sleep(5)


class TestChrome(TestFirefox):
    """ All chrome browser tests inheriting from Firefox Tests. """
    
    def setUp(self):
        self.browser = webdriver.Chrome(
            executable_path=r'browser_tests\chromedriver.exe')
