from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import os
import re
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CDWScraper:
    def __init__(self, config, category):
        """
        Initialize the CDWScraper.

        :param headless: Set to False if you want to see the browser; True for headless mode.
        :param save_directory: Directory to save the extracted product data.
        """
        self.headless = True 
        self.url = config[category].get("url", "")
        self.country = config[category].get("country", "")
        self.website = config[category].get("website", "CDW")
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.save_dir = config.get("save_directory", "save")
        self.filename_with_date = f"{self.website}_{self.country}_{self.date}.json"
        self.response = None

    def execute_search(self, timeout=30000):
        """
        Execute the search on the given URL using Playwright, process the response, and save it to a file.

        :param url: The URL of the website to extract product data from.
        :param timeout: Maximum time (in milliseconds) to wait for the page to load. Default is 30000 ms (30 seconds).
        :return: The extracted product data if successful; None otherwise.
        """
        try:
            with sync_playwright() as p:
                # Launch the browser
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()

                try:
                    # Navigate to the URL
                    page.goto(self.url, timeout=timeout)
                    logger.info(f"Successfully navigated to URL: {self.url}")
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout occurred while trying to load the page: {self.url}")
                    browser.close()
                    return None
                except Exception as e:
                    logger.error(f"Failed to navigate to URL: {self.url}. Error: {e}")
                    browser.close()
                    return None

                # Wait for the search results div to be visible
                try:
                    page.wait_for_selector("div.search-results", timeout=timeout)
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout occurred while waiting for search results to load.")
                    browser.close()
                    return None

                # Process the response and save to file
                product_data = self.process_response(page)

                # Close the browser
                browser.close()
                logger.info("Browser closed successfully.")
                return product_data

        except Exception as e:
            logger.error(f"An error occurred during the Playwright session: {e}")
            return None

    def process_response(self, page):
        """
        Process the response from the search page, extract product data, and save it to a file.

        :param page: The page object returned by the execute_search function.
        :return: A list of dictionaries containing the extracted product data.
        """
        try:
            products = page.query_selector_all("div.search-result")
            product_data = []

            for product in products:
                # Extract MFG# from the mfg-code span
                mfg_code_element = product.query_selector("span.mfg-code")
                mfg_code = mfg_code_element.text_content().replace("MFG#: ", "").strip() if mfg_code_element else "N/A"

                # Extract price from the incentive-saving-container div
                price_element = product.query_selector("div.incentive-saving-conatainer")
                price = price_element.get_attribute("data-price") if price_element else "N/A"

                product_data.append({
                    "sku": mfg_code,
                    "price": price
                })

            logger.info("Successfully extracted product data.")

            # Save the extracted data to a file
            self.save_response_to_file(product_data)
            return product_data

        except Exception as e:
            logger.error(f"Failed to extract product data. Error: {e}")
            return None

    def save_response_to_file(self, response):
        """
        Saves the response (list of hits) to two JSON files.

        :param response: List of results (hits) to be saved.
        """
        if response:
            try:
                # Create 'save' folder if it doesn't exist
                os.makedirs(self.save_dir, exist_ok=True)

                # Save file in 'save' folder with the date
                save_path_with_date = os.path.join(self.save_dir, self.filename_with_date)
                with open(save_path_with_date, "w") as file:
                    json.dump(response, file, indent=4)
                logger.info(f"Response saved to {save_path_with_date}")

            except (IOError, ValueError) as e:
                logger.error(f"Error saving response to file: {e}")
        else:
            logger.warning("No successful response to save.")
