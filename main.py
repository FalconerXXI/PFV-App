import logging
import json
from api_scraper import APIScraper
from products import ProductManager, DirectDialUS, DirectDialCA
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():

    try:
        with open("website_info.json", "r") as file:
            website_info = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading configuration file: {e}")
        return
    
    for category in ["Direct_Dial_CA_Notebooks", "Direct_Dial_CA_Desktops", "Direct_Dial_US_Notebooks", "Direct_Dial_US_Desktops"]:
        search_request = APIScraper(website_info, category)
        search_request.execute_search()
    
    try:
        # Create an engine and session factory
        engine = create_engine('sqlite:///products.db', echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create tables if they do not exist
        Base.metadata.create_all(engine)

        # Initialize managers
        product_manager = ProductManager(session)

        # Load products
        
        #product_manager.load_products_from_json(f'save/DirectDial_CA_Desktops_{(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}.json', DirectDialCA)
        #product_manager.load_products_from_json(f'save/DirectDial_US_Desktops_{(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}.json', DirectDialUS)
        #product_manager.load_products_from_json(f'save/DirectDial_CA_Notebooks_{(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}.json', DirectDialCA)
        #product_manager.load_products_from_json(f'save/DirectDial_US_Notebooks_{(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}.json', DirectDialUS)


        product_manager.load_products_from_json(f'save/DirectDial_CA_Desktops_{datetime.now().strftime("%Y-%m-%d")}.json', DirectDialCA)
        product_manager.load_products_from_json(f'save/DirectDial_US_Desktops_{datetime.now().strftime("%Y-%m-%d")}.json', DirectDialUS)
        product_manager.load_products_from_json(f'save/DirectDial_CA_Notebooks_{datetime.now().strftime("%Y-%m-%d")}.json', DirectDialCA)
        product_manager.load_products_from_json(f'save/DirectDial_US_Notebooks_{datetime.now().strftime("%Y-%m-%d")}.json', DirectDialUS)


    except Exception as e:
        logger.exception("An error occurred in the main function.")
    finally:
        # Close the session
        session.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    main()
