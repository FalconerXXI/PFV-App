from scraper import DirectDialScraper
from cdw_scraper import CDWScraper
from products import DatabaseExporter
from hardware import HardwareScraper
from score import Score
import logging
from fuzzywuzzy import fuzz

def main(): 
    logging.basicConfig(
        level=logging.INFO,  # Set the default logging level
        format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log format
        handlers=[
            logging.FileHandler("app.log"),  # Log to a file called app.log
            logging.StreamHandler()  # Also log to the console
        ]
    )

    # Scrape CPU Scores
    #cpus = HardwareScraper('https://www.cpubenchmark.net/cpu_list.php')
    #cpus.scrape_hardware()

    # Scrape GPU Scores
    #gpu_scraper = HardwareScraper('https://www.videocardbenchmark.net/gpu_list.php')
    #gpu_scraper.scrape_hardware()

    # Scrape Notebooks Specs
    #products = DirectDialScraper('https://www.directdial.com/ca/search/computer-systems/notebooks?sortBy=stock%3Adesc&instock=true&productType=Notebook&productType=Ultrabook&productType=Chromebook&productType=2%20in%201%20Chromebook&productType=Thin%20Client%20Notebook&productType=2%20in%201%20Notebook&productType=Gaming%20Notebook&brand=Dell&brand=HP&brand=Lenovo')
    #products.scrape_product_page()
    #products.scrape_individual_products()

    #cdw_products = CDWScraper('https://www.cdw.com/category/computers/desktops/?w=CA&b=CPQ.DLE.LVO&SortBy=BestMatch&maxrecords=1000&instock=1')
    cdw_products = CDWScraper('https://www.cdw.com/category/computers/laptops-2-in-1s/?w=CB&b=CPQ.DLE.LVO&instock=1&maxrecords=500')
    cdw_products.scrape_product_page()
    cdw_products.scrape_individual_products()
    #cdw_products = CDWScraper('https://www.cdw.com/category/computers/desktops/?w=CA&b=CPQ.DLE.LVO&SortBy=BestMatch&maxrecords=1000&instock=1')
    #cdw_products.scrape_product_page()
    #cdw_products.scrape_individual_products()
    cdw_score = Score('sqlite:///cdw.db', 'sqlite:///hardware.db')
    cdw_score.calculate_scores()

    # Scrape Desktops Specs
    #products = WebScraper('https://www.directdial.com/ca/search/computer-systems/desktop-computers/desktop-computer?instock=true&productType=Desktop%20Computer&brand=Lenovo&brand=Dell&brand=HP')
    #products.scrape_product_page()
    #products.scrape_individual_products()

    #exporter = DatabaseExporter('products.db')
    #exporter.export_table_to_csv('products', 'products.csv')

if __name__ == "__main__":
    main()