from scraper import WebScraper
from products import DatabaseExporter
from hardware import CPU, GPU

def main():
    # Scrape CPU Scores
    cpus = WebScraper('https://www.cpubenchmark.net/cpu_list.php')
    cpus.scrape_hardware()

    # Scrape GPU Scores
    gpu_scraper = WebScraper('https://www.videocardbenchmark.net/gpu_list.php')
    gpu_scraper.scrape_hardware()
    
    # Scrape Notebooks Specs
    #products = WebScraper('https://www.directdial.com/ca/search/computer-systems/notebooks?instock=true&productType=Notebook&productType=Ultrabook&productType=Chromebook&productType=2%20in%201%20Chromebook&productType=Thin%20Client%20Notebook&productType=2%20in%201%20Notebook&productType=Gaming%20Notebook&brand=Dell&brand=HP&brand=Lenovo')
    #products.scrape_product_page()
    #products.scrape_individual_products()

    # Scrape Desktops Specs
    #products = WebScraper('https://www.directdial.com/ca/search/computer-systems/desktop-computers/desktop-computer?instock=true&productType=Desktop%20Computer&brand=Lenovo&brand=Dell&brand=HP')
    #products.scrape_product_page()
    #products.scrape_individual_products()

    #exporter = DatabaseExporter('products.db')
    #exporter.export_table_to_csv('products', 'products.csv')

if __name__ == "__main__":
    main()
 