from datetime import datetime
import json
import logging
import os
import requests

class APIScraper:
    def __init__(self, config, category):
        """
        Initialize the APIScraper object using the JSON configuration.

        :param config: Entire configuration JSON object.
        :param category: Specific category to scrape (e.g., "Direct_Dial_CA_Notebooks").
        """
        self.url = config[category].get("url", "")
        self.querystring = config[category].get("querystring", {})
        self.search_query = config[category].get("search_query", {})
        self.headers = config.get("shared_headers", {})
        self.country = config[category].get("country", "")
        self.website = config[category].get("website", "")
        self.form_type = config[category].get("form_type", "")
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.save_dir = config.get("save_directory", "save")

        # Create two filename variables: one with the date and one without
        self.filename_with_date = f"{self.website}_{self.country}_{self.form_type}_{self.date}.json"
        self.filename_without_date = f"{self.website}_{self.country}_{self.form_type}.json"

        self.save_dir = config.get("save_directory", "save")  # Configurable save directory
        self.response = None
        self.initial_response = None

    def execute_search(self):
        """
        Executes the search request using the provided parameters.
        """
        logger = logging.getLogger(__name__)
        session = requests.Session()
        session.headers.update(self.headers)
        session.params = self.querystring

        payload = {"searches": [self.search_query]}
        payload_json = json.dumps(payload)
        logger.info(f"Starting scan for: {self.website} {self.form_type} {self.country}")

        # Perform the initial request and handle errors
        try:
            self.initial_response = session.post(self.url, data=payload_json, timeout=10)
            self.initial_response.raise_for_status()
            response_data = self.initial_response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error occurred: {conn_err}")
            return
        except requests.exceptions.Timeout:
            logger.error("Request timed out.")
            return
        except ValueError as json_err:
            logger.error(f"Failed to parse response as JSON: {json_err}")
            return

        # Process results from the initial response
        results = response_data.get("results", [])
        if not results or not isinstance(results, list) or len(results) == 0:
            logger.warning("No results found in the response.")
            return

        total_results = results[0].get("found", 0)
        per_page = results[0].get("request_params", {}).get("per_page", 0)
        if per_page == 0:
            logger.warning("No 'per_page' value found in the response.")
            return

        total_pages = (total_results // per_page) + (1 if total_results % per_page != 0 else 0)
        logger.info(f"Total results found: {total_results}")
        logger.info(f"Fetching {total_pages} pages with {per_page} results per page.")

        # Fetch and save all pages of results
        self.fetch_all_pages(total_pages, payload, session)

    def fetch_all_pages(self, total_pages, payload, session):
        """
        Fetch all pages of results and save them to file.

        :param total_pages: Total number of pages to fetch.
        :param payload: Payload to use for each request.
        :param session: Session object for making requests.
        """
        logger = logging.getLogger(__name__)
        all_hits = []
        total_scanned = 0

        for page in range(1, total_pages + 1):
            logger.info(f"Fetching page {page} of {total_pages}...")
            payload["searches"][0]["page"] = page

            try:
                response = session.post(self.url, data=json.dumps(payload), timeout=10)
                response.raise_for_status()
                page_data = response.json()
            except requests.exceptions.HTTPError as http_err:
                logger.error(f"HTTP error on page {page}: {http_err}")
                break
            except requests.exceptions.ConnectionError as conn_err:
                logger.error(f"Connection error on page {page}: {conn_err}")
                break
            except requests.exceptions.Timeout:
                logger.error(f"Request timed out on page {page}.")
                break
            except ValueError as json_err:
                logger.error(f"Failed to parse response as JSON on page {page}: {json_err}")
                break

            # Process results from the current page
            page_results = page_data.get("results", [])
            if page_results:
                hits = page_results[0].get("hits", [])
                all_hits.extend(hits)
                products_scanned = len(hits)
                total_scanned += products_scanned
                logger.info(f"Scanned {products_scanned} products on page {page}.")

        logger.info(f"Total products scanned: {total_scanned}")
        self.save_response_to_file(all_hits)

    def save_response_to_file(self, response):
        """
        Saves the response (list of hits) to two JSON files.
        One in the current directory without the date, and the other in the 'save' folder with the date.

        :param response: List of results (hits) to be saved.
        """
        logger = logging.getLogger(__name__)

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