from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import Select
import undetected_chromedriver as uc
import time
from datetime import datetime
from products import ProductManager, Product
from bs4 import BeautifulSoup
from hardware import HardwareManager, CPU, GPU
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from selenium_stealth import stealth
import random
import re
import traceback
import logging

class CDWScraper:
    def __init__(self, url):
        self.url = url

    def scrape_product_page(self):
        """Scrapes product data from a paginated website."""
        print('Scraping product page')
        options = uc.ChromeOptions()
        options.headless = True
        driver = uc.Chrome(use_subprocess=True, options=options)
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
        driver.get(self.url)
        wait = WebDriverWait(driver, 20)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="main"]/div/div[1]/div[2]/div[6]')))
        wait.until( EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[1]/div[2]/div[6]')))
        container = driver.find_element(By.CLASS_NAME, "search-results")
        products_html = container.get_attribute("innerHTML")
        driver.quit()
        self.extract_product_info(products_html)
    
    def extract_product_info(self, products_html):
        """Extracts product details from the HTML using BeautifulSoup."""
        soup = BeautifulSoup(products_html, 'lxml')
        products = soup.find_all('div', class_='search-result')
        #products = products[0:20]
        for product in products:
            sku = self.extract_sku(product)
            price = self.extract_price(product)
            url = self.extract_url(product)
            updated = datetime.now().strftime("%m/%d/%Y")
            discovered = datetime.now().strftime("%m/%d/%Y")
            product_manager = ProductManager('sqlite:///cdw.db')
            if "notebook" in self.url or "laptop" in self.url:
                type = "notebook"
            elif "desktop" in self.url:
                type = "desktop"
            elif 'workstation' in self.url:
                type = "workstation"
            else:
                type = "N/A"
            product_manager.add_cdw_product(sku, price, type, url, updated, discovered)

    def scrape_individual_products(self):
        print("Scraping individual products")
        engine = create_engine('sqlite:///cdw.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        options = uc.ChromeOptions()
        options.headless = True
        driver = uc.Chrome(use_subprocess=True, options=options)
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
        products_left = True
        while products_left:
            num_products = session.query(Product).filter_by(scanned=False).count()
            scanned_products = 0
            if num_products == 0:
                print("All products have been scanned.")
                break
            print(f"Remaining products to scan: {num_products}")
            num_products = session.query(Product).filter_by(scanned=False).count()
            products = session.query(Product).filter_by(scanned=False).yield_per(1)
            for product in products:
                print(f"Scanning product {scanned_products+1} of {num_products}")
                try:
                    url = product.url
                    specs = {}
                    driver.get(url)
                    time.sleep(.5)
                    driver.refresh()
                    wait = WebDriverWait(driver, 20)
                    try:
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="modal-product-spec"]/div/div/div/div[2]')))
                        wait.until( EC.presence_of_element_located((By.XPATH, '//*[@id="modal-product-spec"]/div/div/div/div[2]')))
                        container = driver.find_element(By.ID, 'TS')
                        try:
                            products_html = container.get_attribute("innerHTML")
                            soup = BeautifulSoup(products_html, 'lxml')
                            spec = soup.find_all('div', class_="panel-row")
                            error = False
                            for row in spec:
                                columns = row.find_all('span')
                                if len(columns) == 2:
                                    label = columns[0].get_text(strip=True)
                                    value = columns[1].get_text(strip=True)
                                    specs[label] = value
                            product.brand = self.extract_brand(specs)
                            product.name = self.extract_name(specs, product.brand)
                            if product.type == "notebook":
                                product.form_factor = self.extract_form_factor_notebook(specs)
                            if product.type == "desktop":
                                product.form_factor = self.extract_form_factor_desktop(specs)
                            if product.type == "workstation":
                                product.form_factor = self.extract_form_factor_desktop(specs)
                            product.cpu = self.extract_cpu(specs)
                            product.ram = self.extract_ram(specs)
                            product.ddr = self.extract_ddr(specs)
                            product.storage = self.extract_storage(specs)
                            product.os = self.extract_os(specs)
                            product.ethernet = self.extract_ethernet(specs)
                            product.gpu = self.extract_gpu(specs)
                            product.wifi = self.extract_wifi(specs)
                            product.touch = self.extract_touch(specs)
                            product.screen_res = self.extract_screen_res(specs)
                            product.screen_type = self.extract_screen_type(specs)
                            product.screen_size = self.extract_screen_size(specs)
                            product.keyboard = self.extract_keyboard(specs)
                            product.warranty = self.extract_warranty(specs)
                            product.error = error
                            if product.cpu == "N/A" or product.gpu == "N/A" or product.form_factor == "N/A":
                                product.error = True
                            if product.storage == 0 or product.ram == 0:
                                product.error = True
                            product.scanned = True
                            session.commit()
                            scanned_products += 1
                            time.sleep(random.uniform(0, 2))
                        except Exception as e:
                            product.scanned = True
                            product.error = True
                            session.commit()
                            logging.error(f"***Error while scanning product {product.id}: {traceback.format_exc()}")
                    except TimeoutException:
                        logging.error(f"***Timeout error on product {product.id} URL: {product.url}")
                        session.rollback()
                        product.error = True
                        product.scanned = True
                        scanned_products += 1
                        session.commit()
                except NoSuchElementException:
                    time.sleep(random.uniform(0, 2))
                    scanned_products += 1
                    session.rollback()
                    logging.error(f"***Error page loading product {product.id}: {traceback.format_exc()}")
        driver.quit()
        session.close()
        logging.info("Scanning complete")

    @classmethod
    def extract_sku(cls, product):
        return product.find('span',class_="mfg-code").find(text=True).strip().replace('MFG#: ', '') if product.find('span',class_="mfg-code") else "N/A"
     
    @classmethod
    def extract_stock(cls, product):
        return product.find_all('div', class_='col-6')[1].find(text=True).strip().replace('Stock: ', '').replace(',', '') if product.find_all('div', class_='col-6')[1] else 0

    @classmethod
    def extract_price(cls, product):
        return product.find('div', class_="price-type-price").find(text=True).strip().replace('$', '').replace(',', '') if product.find('div', class_="price-type-price") else 0

    @classmethod
    def extract_msrp(cls, product):
        return product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.msrp:' in text).find_next(text=True).strip() if product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.msrp:' in text) else 0

    @classmethod
    def extract_rebate(cls, product):
        # Try to find the 'div' containing the rebate info
        rebate_div = product.find('div', class_='in-stock item-alert w-100')
        
        # Check if the div exists
        if rebate_div:
            # Try to find the 'span' inside the div with specific styling
            rebate_span = rebate_div.find('span', style="color:#333e48; font-weight:bold;")
            
            # Check if the span exists
            if rebate_span:
                # Try to find the text inside the span and clean it
                rebate_text = rebate_span.find(text=True)
                if rebate_text:
                    return rebate_text.replace('$', '').strip()
    
    # Return 0 if no rebate info is found
        return 0
    
    @classmethod
    def extract_sale(cls, product):
        sale_div = product.find('div', class_='save-list')
        if sale_div:
            sale_span = sale_div.find('span', class_='save-price')
            if sale_span:
                sale_text = sale_span.find(text=True)
                if sale_text:
                    if 'K' in sale_text:
                        sale_text = sale_text.replace('Save $', '').replace('K', '000').strip()
                    else:
                        sale_text = sale_text.replace('Save $', '').strip()
                    try:
                        return float(sale_text)
                    except ValueError:
                        return 0
        return 0

    @classmethod
    def extract_brand(cls, product):
         return product.get('Brand') if product.get('Brand') else 'N/A'

    @classmethod
    def extract_url(cls, product):
        return "https://www.cdw.com"+product.find('a', class_='search-result-product-url')['href']

    @classmethod
    def extract_name(cls, product, brand):
        line = product.get('Product Line', None)
        series = product.get('Series', product.get('Product Series', None))
        model = product.get('Model', None)
        name_parts = []
        if line:
            name_parts.append(line.strip()+' ')
        if series:
            name_parts.append(series.strip()+' ')
        if model:
            name_parts.append(model.strip()+'')
        if len(name_parts) > 0:
            name = ' '.join(name_parts).replace(brand,'').replace('  ',' ').strip()
        if name == "":
            return "N/A"
        return name
    
    @classmethod
    def extract_category(cls, product):
         return f"{product.get('Product Type', None)}" if product.get('Product Type', None) else 'N/A'

    @classmethod
    def extract_form_factor_notebook(cls, product):
        screen_size = product.get('Screen Size', None)
        if screen_size:
            return int(float(screen_size.lower().replace('"', '').replace('inch','').strip()))
        else:
            return "N/A"
    
    @classmethod
    def extract_form_factor_desktop(cls, product):
        form_factor = product.get('Form Factor', "N/A").strip().lower()
        form_factor_map = {
            "desktop mini": "Tiny",
            "ultra small form factor": "Tiny",
            "micro pc": "Tiny",
            "tiny": "Tiny",
            "mini pc": "Tiny",
            "mini-tower": "SFF",
            "mini tower": "SFF",
            "small form factor": "SFF",
            "sff": "SFF",
            "ultra small": "SFF",
            "tower": "Tower",
            "desktop": "All-in-One",
            "all-in-one": "All-in-One"
        }
        return form_factor_map.get(form_factor, "N/A")

    @classmethod
    def extract_cpu(cls, product):
        processor_brand = product.get('Processor Brand', None)
        processor_type = product.get('Processor Type', None)
        processor_number = product.get('Processor Number', None)
        processor_model = product.get('Processor Model', None)
        overlap_length = 0
        if processor_brand:
            if processor_type:
                if processor_model:
                    max_overlap = min(len(processor_type), len(processor_model))
                    for i in range(max_overlap +1):
                        if processor_type.lower()[-i:] == processor_model.lower()[:i]:
                            overlap_length = i
                    if overlap_length > 1:
                        cpu = processor_brand + ' ' + processor_type+processor_model[overlap_length:]
                    else:
                        cpu = processor_brand + ' ' + processor_type + ' ' + processor_model
                elif processor_number:
                    max_overlap = min(len(processor_type), len(processor_number))
                    for i in range(max_overlap +1):
                        if processor_type.lower()[-i:] == processor_number.lower()[:i]:
                            overlap_length = i
                    if overlap_length > 1:
                        cpu = processor_brand + ' ' + processor_type+processor_number[overlap_length:]
                    else:
                        cpu = processor_brand + ' ' + processor_type + ' ' + processor_number
                else:   
                    cpu = processor_brand + ' ' + processor_type
            else:
                if processor_model:
                    cpu = processor_brand + ' ' + processor_model
                elif processor_number:
                    cpu = processor_brand + ' ' + processor_number
                else:
                    cpu = processor_brand
        else:
            cpu = "N/A"
        return cpu

    @classmethod
    def extract_ram(cls, product):
        return product.get('RAM Installed').upper().replace('GB','').strip() if product.get('RAM Installed') else "N/A"

    @classmethod
    def extract_ddr(cls, product):
        try:
            ddr = product.get('Memory Technology', 'N/A')
            if "ddr4" in ddr.lower():
                return "DDR4"
            elif "ddr5" in ddr.lower():
                return "DDR5"
            else:
                return "N/A"
        except:
            return "N/A"
        
    @classmethod
    def extract_storage(cls, product):
        storage = product.get('Hard Drive Capacity').upper() if product.get('Hard Drive Capacity') else None
        if storage:
            if "GB" in storage:
                storage = int(storage.replace("GB", "").strip())
            elif "TB" in storage:
                storage = int(storage.replace("TB", "").strip())*1000
            return storage
        else:
            return 0

    @classmethod
    def extract_os(cls, product):
        return product.get('Operating System') if product.get('Operating System') else "N/A"

    @classmethod
    def extract_gpu(cls, product):
        shared = product.get("Memory Allocation Technology", None)
        graphics_controller_model = product.get("Graphics Controller Model", None)
        if shared:
            if "shared" in shared.lower():
                return "Integrated"
        if graphics_controller_model:
            gpu_clean = re.sub(r'\d+', '', graphics_controller_model).lower().replace('intel', '').strip()
            if gpu_clean == "uhd graphics" or gpu_clean == "iris xe graphics" or gpu_clean == "graphics":
                return "Integrated"
            else:
                if "/" in graphics_controller_model:
                    temp = graphics_controller_model.split("/")
                    if "uhd graphics" in temp[0].lower():
                        return temp[1].strip()
                    else:
                        return temp[0].strip()
                else:
                    return graphics_controller_model
        else:
            return "N/A"

    @classmethod
    def extract_screen_res(cls, product):
        screen_resolution_abv = product.get('Display Resolution Abbreviation', None)
        screen_resolution = product.get('Native Resolution', None)
        if screen_resolution_abv:
            return screen_resolution_abv
        elif screen_resolution:
            return screen_resolution
        else:
            return "N/A"
    
    @classmethod
    def extract_screen_type(cls, product):
        return product.get('TFT Technology', "N/A")
    
    @classmethod
    def extract_screen_size(cls, product):
        screen_size = product.get('Screen Size', None)
        if screen_size:
            return int(float(screen_size.lower().replace('"', '').replace('inch','').strip()))
        else:
            return "N/A"

    @classmethod
    def extract_wifi(cls, product):
        wifi = product.get('Wireless LAN', "N/A").lower()
        if "802" in wifi or 'yes' in wifi:
            wifi = "Yes"
        else:
            wifi = "No"
        return wifi

    @classmethod
    def extract_keyboard(cls, product):
        return product.get('Keyboard Localization', "N/A")

    @classmethod
    def extract_touch(cls, product):
        touch = product.get('Touchscreen', None)
        if touch:
            return touch
        else:
            return "N/A"

    @classmethod
    def extract_ethernet(cls, product):
        ethernet = product.get('Data Link Protocols', "N/A").lower()
        if "ethernet" in ethernet:
            ethernet = "Yes"
        else:
            ethernet = "No"
        return ethernet
    
    @classmethod
    def extract_warranty(cls, product):
        warranty = product.get('Limited Warranty', product.get('Bundled Services', None))
        if warranty:
            warranty = warranty.lower()
            match = re.search(r'(\d+)\s*(?=year[s]?\b)', warranty.lower())
            if match:
                return int(match.group(1))
            else:
                return 0
        else:
            return 0