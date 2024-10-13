from datetime import datetime
import json
import logging
import os
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more verbose output
logger = logging.getLogger(__name__)

class InsightAPIScraper:
    def __init__(self, config, category):
        """
        Initialize the InsightAPIScraper object using the JSON configuration.

        :param config: Configuration JSON object.
        """
        # Define the Insight-specific category
        self.url = config[category].get("url", "")
        self.querystring = config[category].get("querystring", {})
        self.headers = config.get("shared_headers", {})
        self.country = config[category].get("country", "")
        self.website = config[category].get("website", "Insight")
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.save_dir = config.get("save_directory", "save")
        self.filename_with_date = f"{self.website}_{self.country}_{self.date}.json"
        self.response = None

    def execute_search(self):
        """
        Executes the search request using the provided parameters.
        """
        logger.info(f"Starting scan for: {self.website} {self.country}")
        try:
            logger.debug(f"Request URL: {self.url}")
            self.response = requests.get(self.url, headers=self.headers, params=self.querystring)
            self.response.raise_for_status()

            # Log the response
            logger.debug(f"Response Status Code: {self.response.status_code}")
            #logger.debug(f"Response Text: {self.response.text}")

            # Process response data
            response_data = self.response.json()
            self.process_response(response_data)

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout:
            logger.error("Request timed out.")
        except ValueError as json_err:
            logger.error(f"Failed to parse response as JSON: {json_err}")

    def process_response(self, response_data):
        """
        Process the response from the search page, extract product data, and save it to a file.

        :param page: The page object returned by the execute_search function.
        :return: A list of dictionaries containing the extracted product data.
        """
        logger.info("Processing response data...")
        try:
            results = response_data.get("products", [])
            product_data = []

            for product in results:
                # Extract MFG# from the mfg-code span
                sku = product.get("sku", "N/A")
                price = product.get("insightPrice", "N/A")

                product_data.append({
                    "sku": sku,
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

