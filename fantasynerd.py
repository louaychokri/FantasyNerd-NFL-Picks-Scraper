from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
import time


class Fantasynerd:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.chrome_options.add_argument("--ignore-certificate-errors")  
        self.chrome_options.add_argument("--disable-notifications")  
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
       
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        self.base_url = "https://www.fantasynerds.com/nfl/picks/"
        self.driver.get(self.base_url + "1")
        print(f"Successfully navigated to {self.base_url + '1'}")
     
        self.connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root123',
            database='fantasy'
        )
        self.cursor = self.connection.cursor()
        print("Database connected successfully.")
       
        self.urls = [] 
        self.details = []  
        self.seen_urls = set() 

        self.winner = []


    def scroll_page(self):
        print("Starting page scroll...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            print(f"Scrolled to height: {new_height}")
            if new_height == last_height:
                print("Scrolling completed, all content loaded.")
                break
            last_height = new_height


    def get_pages_url(self):
        print("Fetching pagination URLs...") 
        self.driver.get(self.base_url + "1")
        urls = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located((By.ID, "desktopMenu"))
        )
        self.urls = []
        for url in urls:
            links = url.find_elements(By.TAG_NAME, "a")
            for i, link in enumerate(links):
                href = link.get_attribute("href")
                if href and href.startswith(self.base_url) and href not in self.urls:
                    self.urls.append(href)
                    print(f"Page URL {i+1}: {href}")
                   

    def fetch_page_data(self, url):
        self.driver.get(url)
        print(f"Successfully navigated to {url}")
        self.scroll_page()
    
        containers = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "top"))
        )
        print(f"Found {len(containers)} product containers with class 'top'.")
        
        for i, container in enumerate(containers):
            links = container.find_elements(By.TAG_NAME, "a")
            for j, link in enumerate(links):
                href = link.get_attribute("href")   
                expected_prefix = f"https://www.fantasynerds.com/nfl/picks/{url.split('/')[-1]}/"
                if href and href.startswith(expected_prefix) and not any(x in href for x in ["bsky.app", "facebook.com", "x.com"]):
                    if href not in self.seen_urls:
                        self.seen_urls.add(href)
                        self.details.append(href)
                        print(f"Found product {j+1} in container {i+1}: URL={href}")
                    

    def fetch_product_data(self, href):
        self.driver.get(href)
        print(f"Successfully navigated to {href}")
        self.scroll_page()
        winner = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "pad"))).text.strip()
        print(winner)
        self.save_to_db(winner)
        
    
    def save_to_db(self, winner):
        names_list = (winner,)
        self.cursor.execute(f"INSERT INTO nerd (name) VALUE (%s)", names_list)
        self.connection.commit()
        print(f"{winner} was added successfully")
            

    def scrape_all_pages(self):
        self.get_pages_url() 
        for i, url in enumerate(self.urls):
            print(f"\nProcessing page {i+1}/{len(self.urls)}")
            self.fetch_page_data(url)
           
        for j, href in enumerate(self.details):
            print(f"\nFetching product {j+1}/{len(self.details)}")
            self.fetch_product_data(href)

     
    def close(self):
        self.driver.quit()
        print("WebDriver closed.")


if __name__ == "__main__":
    scraper = None
    try:
        scraper = Fantasynerd()
        scraper.scrape_all_pages()
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        if scraper:
            scraper.close()