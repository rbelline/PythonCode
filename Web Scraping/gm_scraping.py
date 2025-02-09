import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GoogleMapsScraper:

    location_data = {}

    def __init__(self):
        # Automatically install the chromedriver
        chromedriver_autoinstaller.install()

        # Set up Chrome options
        self.options = Options()
        # self.options.add_argument("--headless") # Uncomment this line to run headless
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--remote-debugging-port=9222")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36")
        self.service = Service("/usr/bin/google-chrome") # Ensure correct Chrome path
        
        # Initialize the Chrome driver
        self.driver = webdriver.Chrome(options=self.options)

        # Initialize location data
        # self.location_data["rating"] = "NA"
        # self.location_data["reviews_count"] = "NA"
        # self.location_data["location"] = "NA"
        # self.location_data["contact"] = "NA"
        # self.location_data["website"] = "NA"
        # self.location_data["Time"] = {"Monday":"NA", "Tuesday":"NA", "Wednesday":"NA", "Thursday":"NA", "Friday":"NA", "Saturday":"NA", "Sunday":"NA"}
        # self.location_data["Reviews"] = []
        # self.location_data["Popular Times"] = {"Monday":[], "Tuesday":[], "Wednesday":[], "Thursday":[], "Friday":[], "Saturday":[], "Sunday":[]}

    def open_google_maps(self):
        # Open Google Maps
        self.driver.get("https://www.google.com/maps")
        print("Google Maps opened")
    
    def accept_cookies(self):
        try:
            # Increase timeout for loading the cookies consent button
            print("Waiting for cookies consent button...")
            # Try CSS Selector instead of XPath
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, "[aria-label='Accetta tutto']")
            # Attempt to click using Selenium
            cookie_button.click()
            print("Cookies accepted")
        except NoSuchElementException:
            print("No GDPR requirements detected")

    def search_location(self, location):
        # Find the search bar and input the location
        search_box = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#searchboxinput"))
            )
        search_box.send_keys(location)
        search_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Cerca']")
        search_button.click()
        print(f"Searching for {location}...")
    

if __name__ == "__main__":
    scraper = GoogleMapsScraper()
    scraper.open_google_maps()
    scraper.accept_cookies()
    scraper.search_location("Italian restaurants")
    time.sleep(20)