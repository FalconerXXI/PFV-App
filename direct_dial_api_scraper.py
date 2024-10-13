from datetime import datetime
import json
import logging
import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import math

class DirectDialAPIScraper:
    def __init__(self, config, category):
        self.url = config[category].get("url", "")
        self.querystring = config[category].get("querystring", {})
        if not isinstance(self.querystring, dict):
            raise ValueError("Expected 'querystring' to be a dictionary.")
        self.search_query = config[category].get("search_query", {})
        self.headers = config.get("shared_headers", {})
        self.country = config[category].get("country", "")
        self.website = config[category].get("website", "")
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.save_dir = config.get("save_directory", "save")
        self.filename_with_date = f"{self.website}_{self.country}_{self.date}.json"
        self.response = None
        self.initial_response = None

    def execute_search(self):
        logger = logging.getLogger(__name__)
        with requests.Session() as session:
            session.headers.update(self.headers)
            session.params = self.querystring
            payload = {"searches": [self.search_query]}
            logger.info(f"Starting scan for: {self.website} {self.country}")
            try:
                self.initial_response = self.fetch_page_with_retry(self.url, payload, session)
                response_data = self.initial_response
            except requests.exceptions.RequestException as err:
                logger.error(f"Request error occurred: {err}")
                return
            results = response_data.get("results", [])
            if not results or not isinstance(results, list) or len(results) == 0:
                logger.warning("No results found in the response.")
                return
            total_results = results[0].get("found", 0)
            per_page = results[0].get("request_params", {}).get("per_page", 0)
            if per_page == 0:
                logger.warning("No 'per_page' value found in the response.")
                return
            total_pages = math.ceil(total_results / per_page)
            logger.info(f"Total results found: {total_results}")
            logger.info(f"Fetching {total_pages} pages with {per_page} results per page.")
            self.fetch_all_pages(total_pages, payload, session)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_page_with_retry(self, url, payload, session):
        response = session.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def fetch_all_pages(self, total_pages, payload, session):
        logger = logging.getLogger(__name__)
        all_hits = []
        total_scanned = 0
        for page in range(1, total_pages + 1):
            logger.info(f"Fetching page {page} of {total_pages}...")
            payload["searches"][0]["page"] = page
            try:
                page_data = self.fetch_page_with_retry(self.url, payload, session)
            except requests.exceptions.RequestException as err:
                logger.error(f"Request error on page {page}: {err}")
                break
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
        logger = logging.getLogger(__name__)
        if response:
            try:
                os.makedirs(self.save_dir, exist_ok=True)
                save_path_with_date = os.path.join(self.save_dir, self.filename_with_date)
                with open(save_path_with_date, "w", encoding="utf-8") as file:
                    json.dump(response, file, indent=4)
                logger.info(f"Response saved to {save_path_with_date}")

            except (IOError, ValueError, OSError) as e:
                logger.error(f"Error saving response to file: {e}")
        else:
            logger.warning("No successful response to save.")

