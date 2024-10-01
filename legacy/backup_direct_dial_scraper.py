# Standard Library Imports
import json
import logging
from urllib.parse import urlparse
from datetime import datetime
from playwright.sync_api import sync_playwright

class DirectDialScraper:
    def __init__(self, base_url, api_url, db):
        self.base_url = base_url
        self.api_url = api_url
        self.db = db

    def capture_post_api_response_and_save(self):
        # Configure logging settings
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Extract domain name from the base URL for file naming
        parsed_url = urlparse(self.base_url)
        domain_name = parsed_url.netloc.replace("www.", "").replace(".", "-")

        # Generate filename based on domain and current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        json_filename = f"products_{domain_name}_{current_date}.json"

        with sync_playwright() as p:
            try:
                # Launch the browser with additional flags to reduce detection and debugging enabled
                browser = p.chromium.launch(
                    headless=True,  # Set to True for headless mode, False for visual debugging
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-gpu",
                        "--no-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )

                # Create a new browser context with custom settings
                context = browser.new_context(
                    viewport={"width": 1366, "height": 768},  # Set screen size
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"  # Set custom User-Agent
                )

                # Create a new page within this context
                page = context.new_page()

                # Inject JavaScript to override headless properties
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

                # Variable to store the captured response
                captured_response = None

                # Handler to capture POST requests
                def handle_request(request):
                    if request.method == "POST" and self.api_url in request.url:
                        logging.info(f"Captured POST Request to {request.url}")
                        logging.info(f"Request Payload: {request.post_data[:100]}") if request.post_data else None

                # Handler to capture POST responses
                def handle_response(response):
                    nonlocal captured_response
                    if self.api_url in response.url:
                        try:
                            captured_response = response.json()
                            logging.info(f"Captured Response from {response.url} with status {response.status}")
                            hits = captured_response.get("results", [{}])[0].get("hits", [])
                            logging.info(f"'hits' list contains {len(hits)} items.")
                        except Exception as e:
                            captured_response = response.text()
                            logging.error(f"Error parsing JSON: {e}")

                # Set up event listeners for request and response
                page.on("request", handle_request)
                page.on("response", handle_response)

                # Extract the URL structure for pagination
                query_index = self.base_url.find("?")

                # Start with the first page
                page_number = 1
                products = []  # List to hold all products across pages

                while True:
                    # Construct URL by inserting "page={page_number}&" after the "?"
                    paginated_url = f"{self.base_url[:query_index]}?page={page_number}&{self.base_url[query_index+1:]}"
                    logging.info(f"Navigating to {paginated_url}")
                    logging.info(f"Scanning page {page_number}...")  # Log which page is being scanned

                    # Navigate to the current page URL
                    try:
                        page.goto(paginated_url, timeout=60000)  # Increase timeout to 60 seconds
                        logging.info(f"Successfully navigated to {paginated_url}")
                    except Exception as e:
                        logging.error(f"Navigation error: {e}")
                        break

                    # Wait for the network to be idle to ensure all requests complete
                    try:
                        page.wait_for_load_state("networkidle", timeout=30000)  # 30 seconds timeout
                        logging.info(f"Page {page_number} load completed.")
                    except Exception as e:
                        logging.error(f"Error waiting for load state: {e}")
                        break

                    # Check if any response was captured and if it contains items
                    if captured_response:
                        if isinstance(captured_response, dict) and "results" in captured_response:
                            # Extract only the products in the first occurrence of "hits"
                            hits = captured_response.get("results", [{}])[0].get("hits", [])
                            if not hits:
                                logging.info(f"Empty 'hits' list on page {page_number}. No more items to capture. Exiting loop.")
                                break
                            else:
                                logging.info(f"Captured {len(hits)} items from page {page_number}.")
                                products.extend(hits)  # Append products from current page to the list

                        else:
                            logging.info(f"No valid 'results' or 'hits' structure found in the response on page {page_number}. Exiting loop.")
                            break
                    else:
                        logging.info(f"No response captured on page {page_number} or no matching POST request found. Exiting loop.")
                        break

                    # Increment to the next page
                    page_number += 1

                # Close the browser after capturing the response
                try:
                    browser.close()
                    logging.info("Browser closed successfully.")
                except Exception as e:
                    logging.error(f"Error closing the browser: {e}")

                # Save the captured products to a JSON file
                if products:
                    with open(json_filename, 'w', encoding='utf-8') as json_file:
                        json.dump(products, json_file, indent=4, ensure_ascii=False)
                    logging.info(f"All captured products have been saved to {json_filename}.")
                else:
                    logging.info("No products to save.")

            except Exception as e:
                logging.error(f"An error occurred: {e}")
