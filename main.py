import logging
import json
from direct_dial_api_scraper import DirectDialAPIScraper
from insight_scraper_api import InsightAPIScraper
from products import ProductManager, DirectDialUS, DirectDialCA
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from datetime import datetime, timedelta
from cdw_scraper_html import CDWScraper
from hardware_scraper_api import HardwareBenchmarkScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    ### DIRECT DIAL SCRAPING ###
    try:
        with open("direct_dial_website_info.json", "r") as file:
            website_info = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading configuration file: {e}")
        return
    
    for category in ["Direct_Dial_US", "Direct_Dial_CA", ]:
        search_request = DirectDialAPIScraper(website_info, category)
        search_request.execute_search()

    ### INSIGHT SCRAPING ###
    try:
        with open("insight_website_info.json", "r") as file:
            website_info = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading configuration file: {e}")
        return
    
    for category in ["Insight_US", "Insight_CA"]:
        search_request = InsightAPIScraper(website_info, category)
        search_request.execute_search()
    

    ### CDW SCRAPING ###
    try:
        with open("cdw_website_info.json", "r") as file:
            cdw_website_info = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading configuration file: {e}")
        return
    for category in ["CDW_US", "CDW_CA"]:
        search_request = CDWScraper(cdw_website_info, category)
        search_request.execute_search()

    ### BUILD DATABASE ###
    try:
        engine = create_engine('sqlite:///products.db', echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        Base.metadata.create_all(engine)
        product_manager = ProductManager(session)
        product_manager.load_products_from_json(f'save/DirectDial_CA_{datetime.now().strftime("%Y-%m-%d")}.json', DirectDialCA)
        product_manager.load_products_from_json(f'save/DirectDial_US_{datetime.now().strftime("%Y-%m-%d")}.json', DirectDialUS)
    except Exception as e:
        logger.exception("An error occurred in the main function.")
    finally:
        session.close()
        logger.info("Database session closed.")

    ### HARDWARE BENCHMARK SCRAPING ###
    scraper = HardwareBenchmarkScraper("hardware_website_info.json")
    scraper.run()

    

if __name__ == "__main__": 
    main()
