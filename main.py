from direct_dial_scraper import DirectDialScraper
from cdw_scraper import CDWScraper
from insight_scraper import InsightScraper
from products import DatabaseExporter
from hardware import HardwareScraper
from score import Score
import logging

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
    #cdw_products = CDWScraper('https://www.cdw.com/category/computers/laptops-2-in-1s/?w=CB&b=CPQ.DLE.LVO&instock=1&maxrecords=500')
    #cdw_products.scrape_product_page()
    #cdw_products.scrape_individual_products()
    #cdw_products = CDWScraper('https://www.cdw.com/category/computers/desktops/?w=CA&b=CPQ.DLE.LVO&SortBy=BestMatch&maxrecords=1000&instock=1')
    #cdw_products.scrape_product_page()
    #cdw_products.scrape_individual_products()
    #cdw_score = Score('sqlite:///cdw.db', 'sqlite:///hardware.db')
    #cdw_score.calculate_scores()

    # Scrape DirectDial
    products = DirectDialScraper('https://www.directdial.com/ca/search/computer-systems?instock=true&productType=Desktop%20Computer&brand=Dell&brand=Lenovo&brand=HP')
    products.scrape_product_page()
    products.scrape_individual_products()

    # Scrape Insight
    #products = InsightScraper('https://ca.insight.com/en_CA/search.html?country=CA&q=*%3A*&instockOnly=false&selectedFacet=Header_Manufacturer_A00630_en_US_s%3ALenovo%7CDell%7C%22HP+Inc.%22%2CCategoryPath_en_US_ss_lowest_s%3ALaptops%7C%22Mobile+Workstations%22%7CWorkstations%7CDesktops%7C%22Thin+Client+Desktops%22%7CChromebooks%7C%22Small+Form+Factor+Desktops%22%7C%22Mini+Desktops%22%7CUltrabooks%7C%22All-in-One+Computers%22%7C%22Thin+Client+Laptops%22%7C%22Desktops+Tower%22%7C%22Flip+Design+Laptops%22&start=0&salesOrg=4100&lang=en_US&rows=1000&userSegment=CES&tabType=products')
    #products.scrape_product_page()
    #products.scrape_individual_products()

    #exporter = DatabaseExporter('products.db')
    #exporter.export_table_to_csv('products', 'products.csv')

if __name__ == "__main__":
    main()