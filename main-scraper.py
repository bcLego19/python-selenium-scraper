import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import time

# Configuration steps

script_dir = os.path.dirname(__file__)

# For Windows:
CHROMEDRIVER_PATH = os.path.join(script_dir, 'drivers', 'chromedriver.exe')
# For Linux/macOS:
# CHROMEDRIVER_PATH = os.path.join(script_dir, 'drivers', 'chromedriver')

TARGET_URL = "https://quotes.toscrape.com/"
MONGODB_URI = "mongodb://localhost:27017/"
DB_NAME = "quotes_db"
COLLECTION_NAME = "famous_quotes"

# Initialize WebDriver (Selenium)

driver = None 
try:
	print(f"Attempting to start Chrome with driver from: {CHROMEDRIVER_PATH}")
	# Use service to specify executable path
	service = ChromeService(executable_path=CHROMEDRIVER_PATH)
	driver = webdriver.Chrome(service=service)
	print("WebDriver initialized successfully.")

	# Maximize window for better visibility
	driver.maximize_window()

	# Navigate to target URL
	print(f"Navigating to: {TARGET_URL}")
	driver.get(TARGET_URL)
	print("Page loaded.")

	# Scrape Data
	print("Starting Data Extraction...")
	quotes_data = []

	for page_num in range(1, 4):
		print(f"Scraping page {page_num}")

		WebDriverWait(driver, 10).until(
			EC.presence_of_all_elements_located((By.CLASS_NAME, "quote"))
			)

		quotes = driver.find_elements(By.CLASS_NAME, "quote")

		for quote_element in quotes:
			try:
				text = quote_element.find_element(By.CLASS_NAME, "text").text
				author = quote_element.find_element(By.CLASS_NAME, "author").text

				tags_elements = quote_element.find_elements(By.CLASS_NAME, "tag")
				tags = [tag.text for tag in tags_elements]

				quotes_data.append({
					"text": text,
					"author": author,
					"tags": tags,
					"source_url": driver.current_url
					})
			except Exception as e:
				print(f"Error extracting data from a quote element: {e}")
				continue

		if page_num < 3:
			try:
				next_button = WebDriverWait(driver, 5).until(
					EC.element_to_be_clickable((By.CLASS_NAME, "next"))
					)
				next_button.find_element(By.TAG_NAME, "a").click()
				print("Clicked 'Next' button.")
				time.sleep(2)
			except Exception:
				print("No 'Next' button found or could not click. Assuming last page.")
				break
		else:
			print("Finished desired number of pages.")

	print(f"Scraping completed. Found {len(quotes_data)} quotes.")

	# Connect to MongoDB and Store Data
	print("Connecting to MongoDB...")
	client = MongoClient(MONGODB_URI)
	db = client[DB_NAME]
	collection = db[COLLECTION_NAME]

	if quotes_data:
		result = collection.insert_many(quotes_data)
		print(f"Successfully inserted {len(result.inserted_ids)} documents into '{COLLECTION_NAME}' collection.")
	else:
		print("No data to insert into MongoDB")

except Exception as e:
	print(f"An error occurred during the scraping process: {e}")
	import traceback
	traceback.print_exc()

finally:
	# Clean up
	if driver:
		print("Closing WebDriver...")
		driver.quit()

	if 'client' in locals() and client:
		print("Closing MongoDB connection...")
		client.close()
	print("Script finished.")