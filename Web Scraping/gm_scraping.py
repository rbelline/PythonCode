import re
import time
import chromedriver_autoinstaller

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
        self.driver.get("https://www.google.com/maps/?hl=en")
        print("Google Maps opened")
    
    def accept_cookies(self):
        try:
            # Increase timeout for loading the cookies consent button
            print("Waiting for cookies consent button...")
            # Try CSS Selector instead of XPath
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, "[aria-label='Accept all']")
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
        search_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Search']")
        search_button.click()
        print(f"Searching for {location}...")

    def get_location_data(self):
        #Ensure the element load before getting the data
        business_items = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@role="feed"]//div[contains(@jsaction, "mouseover:pane")]'))
            )
        print(f"Found {len(business_items)} businesses")
        return business_items

    def get_business_data(self, business_items):
        data = []
        for item in business_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall").text
                link = item.find_element(By.CSS_SELECTOR, "a[jsaction]").get_attribute("href")
                # Append each business's data to the list
                data.append({
                    'name': name,
                    'link': link
                })
            except Exception as e:
                print(f"Error: {e}")
        return data

    def get_business_reviews_and_rating(self, business_items, basic_data):
        for item in business_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall").text
                reviews_element = item.find_element(By.CSS_SELECTOR, "span[role='img']")
                reviews_text = reviews_element.get_attribute("aria-label")
                match = re.match(r"(\d+\.\d+) stars (\d+[,]*\d+) Reviews", reviews_text)
                if match:
                    stars = float(match.group(1))
                    review_count = int(match.group(2).replace(",", ""))
                    # Find the correct business in the list and update with reviews and ratings
                    for business in basic_data:
                        if business["name"] == name:
                            business["rating"] = stars
                            business["reviews"] = review_count
                            print(f"Rating for {name}: {stars}, Reviews: {review_count}")

            except Exception as e:
                print(f"Error: {e}")
        return basic_data
    
    def get_contact_and_website(self, business_items, basic_data):
        for item in business_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall").text
                info_div = item.find_element(By.CSS_SELECTOR, ".fontBodyMedium")
                address_button = info_div.find_element(By.XPATH, ".//button[contains(@aria-label, 'Address')]")
                address = address_button.get_attribute("aria-label").replace('Address: ', '') if address_button else None

                # Update business data
                for business in basic_data:
                    if business["name"] == name:
                        business["contact"] = address
                        # business["website"] = website
                        print(f"Contact for {name}: {address}")

            except Exception as e:
                print(f"Error: {e}")
        return basic_data
    
    # def additional_business_data(self, business_items, basic_data):
    #     for item in business_items:
    #         try:
    #             name = item.find_element(By.CSS_SELECTOR, "div.fontHeadlineSmall").text
    #             info_div = item.find_element(By.CSS_SELECTOR, ".fontBodyMedium")
    #             spans = info_div.find_elements(By.XPATH, ".//span[not(@*) or @style]")
    #             details = [span.text for span in spans if span.text.strip()]
    #             if details:
    #                 for business in basic_data:
    #                     if business["name"] == name:
    #                         business["details"] = details
    #                         print(f"Details for {name}: {details}")

    #         except Exception as e:
    #             print(f"Error: {e}")
    #     return basic_data

if __name__ == "__main__":
    scraper = GoogleMapsScraper()
    scraper.open_google_maps()
    scraper.accept_cookies()
    scraper.search_location("Italian restaurants")

    business_items = scraper.get_location_data()
    header_data = scraper.get_business_data(business_items)
    scoring_data = scraper.get_business_reviews_and_rating(business_items, header_data)
    contact_data = scraper.get_contact_and_website(business_items, header_data)
    # additional_data = scraper.additional_business_data(business_items, header_data)

    print(contact_data)
    time.sleep(20)