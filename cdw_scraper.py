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
from ai_scraper import AIScraper
import random
import re
import traceback
import logging

class CDWScraper:
    def __init__(self, url):
        self.url = url

    def scrape_product_page(self):
        print('Scraping product page')
        driver = self.setup_driver()
        self.navigate_to_page(driver)
        item = '.search-results'
        self.wait_for_elements(driver, item, timeout=5)
        products_html = self.extract_html(driver)
        driver.quit()
        self.extract_product_info(products_html)

    def setup_driver(self):
        options = uc.ChromeOptions()
        options.headless = False
        driver = uc.Chrome(use_subprocess=True, options=options)
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
        return driver
    
    def navigate_to_page(self, driver):
        driver.get(self.url)

    def extract_html(self, driver):
        self.wait_for_elements(driver, '.search-results', timeout=5)
        container = driver.find_element(By.CLASS_NAME, "search-results")
        return container.get_attribute("innerHTML")
    
    def extract_product_info(self, products_html):
        soup = BeautifulSoup(products_html, 'lxml')
        products = soup.find_all('div', class_='search-result')
        products = products[0:15]
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

    def wait_for_elements(self, driver, item_class, timeout):
        wait = WebDriverWait(driver, timeout)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, item_class)))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, item_class)))

    def scrape_individual_products(self):
        engine = create_engine('sqlite:///cdw.db')
        session = sessionmaker(bind=engine)()
        driver = self.setup_driver()
        while True:
            num_products = session.query(Product).filter_by(scanned=False).count()
            if num_products == 0:
                print("All products have been scanned.")
                break
            print(f"Remaining products to scan: {num_products}")
            products = session.query(Product).filter_by(scanned=False).yield_per(1)
            for product in products:
                print(f"Scanning product {product.sku}")
                self.scan_product(driver, product, session)
        driver.quit()
        session.close()
        logging.info("Scanning complete")

    def scan_product(self, driver, product, session):
        try:
            url = product.url
            specs = {}
            driver.get(url)
            item_class = ".accordion-wrapper"
            try:
                self.wait_for_elements(driver, item_class, timeout=5)
            except TimeoutException:
                logging.info(f"First attempt failed for product {product.sku}, refreshing page...")
                driver.refresh()
                try:
                    self.wait_for_elements(driver, item_class, timeout=5)
                except TimeoutException:
                    logging.error(f"Second attempt failed for product {product.sku}, moving on...")
                    product.scanned = True
                    product.error = True
                    session.commit()
                    return
            self.extract_product_specs(driver, specs, product.type)
            self.update_product_in_db(product, specs, session)
        
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error scanning product {product.sku}: {traceback.format_exc()}")
            product.scanned = True
            product.error = True
            session.commit()

    def extract_product_specs(self, driver, specs, type):
        """Extracts the product specs using Selenium and BeautifulSoup."""
        unrefined_data = {}
        try:
            container = driver.find_element(By.ID, 'TS')
            specs_html = container.get_attribute("innerHTML")
            soup = BeautifulSoup(specs_html, 'html.parser')
            rows = soup.find_all('div', class_="panel-row")
            for row in rows:
                columns = row.find_all('span')
                if len(columns) == 2:
                    label = columns[0].get_text(strip=True)
                    value = columns[1].get_text(strip=True)
                    unrefined_data[label] = value
            specs['brand'] = self.extract_brand(unrefined_data)
            specs['name'] = self.extract_name(unrefined_data, specs['brand'])
            specs['form_factor'] = self.extract_form_factor(unrefined_data, type)
            specs['cpu'] = self.extract_cpu(unrefined_data)
            specs['gpu'] = self.extract_gpu(unrefined_data)
            specs['storage'] = self.extract_storage(unrefined_data)
            specs['ram'] = self.extract_ram(unrefined_data)
            specs['keyboard'] = self.extract_keyboard(unrefined_data)
            specs['warranty'] = self.extract_warranty(unrefined_data)
            specs['ddr'] = self.extract_ddr(unrefined_data)
            specs['os'] = self.extract_os(unrefined_data)
            specs['ethernet'] = self.extract_ethernet(unrefined_data)
            specs['wifi'] = self.extract_wifi(unrefined_data)
            specs['screen_resolution'] = self.extract_screen_res(unrefined_data)          
            specs['screen_type'] = self.extract_screen_type(unrefined_data)
            specs['screen_size'] = self.extract_screen_size(unrefined_data)
            specs['touch'] = self.extract_touch(unrefined_data)

        except NoSuchElementException as e:
            logging.error(f"Error extracting product specs: {traceback.format_exc()}")
            specs['brand'] = specs.get('brand', 'N/A')
            specs['name'] = specs.get('name', 'N/A')
            specs['form_factor'] = specs.get('form_factor', 'N/A')
            specs['cpu'] = specs.get('cpu', 'N/A')
            specs['gpu'] = specs.get('gpu', 'N/A')
            specs['storage'] = specs.get('storage', 0)
            specs['ram'] = specs.get('ram', 0)
            specs['warranty'] = specs.get('warranty', 'N/A')
            specs['ddr'] = specs.get('ddr', 'N/A')
            specs['os'] = specs.get('os', 'N/A')
            specs['ethernet'] = specs.get('ethernet', 'N/A')
            specs['wifi'] = specs.get('wifi', 'N/A')
            specs['keyboard'] = specs.get('keyboard', 'N/A')
            specs['screen_resolution'] = specs.get('screen_resolution', 'N/A')
            specs['screen_size'] = specs.get('screen_size', 'N/A')
            specs['screen_type'] = specs.get('screen_type', 'N/A')
            specs['touch'] = specs.get('touch', 'N/A')

    def update_product_in_db(self, product, specs, session):
        try:
            product.brand = specs.get('brand', 'N/A')
            product.name = specs.get('name', 'N/A')
            product.form_factor = specs.get('form_factor', 'N/A')
            product.cpu = specs.get('cpu', 'N/A')
            product.gpu = specs.get('gpu', 'N/A')
            product.storage = specs.get('storage', 0)
            product.ram = specs.get('ram', 0)
            product.keyboard = specs.get('keyboard', 'N/A')
            product.warranty = specs.get('warranty', 'N/A')
            product.ddr = specs.get('ddr', 'N/A')
            product.os = specs.get('os', 'N/A')
            product.ethernet = specs.get('ethernet', 'N/A')
            product.wifi = specs.get('wifi', 'N/A')
            product.screen_resolution = specs.get('screen_resolution', 'N/A')
            product.screen_size = specs.get('screen_size', 'N/A')
            product.screen_type = specs.get('screen_type', 'N/A')
            product.touch = specs.get('touch', 'N/A')

            product.scanned = True
            if product.cpu == "N/A" or product.gpu == "N/A" or product.storage == 0 or product.ram == 0:
                product.error = True
            session.commit()
        except Exception as e:
            logging.error(f"Error updating product {product.sku} in the database: {traceback.format_exc()}")
            session.rollback()  

        
    @classmethod
    def extract_sku(cls, product):
        return product.find('span',class_="mfg-code").find(text=True).strip().replace('MFG#: ', '') if product.find('span',class_="mfg-code") else "N/A"
     
    @classmethod
    def extract_brand(cls, product):
         return product.get('Brand') if product.get('Brand') else 'N/A'

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
    def extract_url(cls, product):
        return "https://www.cdw.com"+product.find('a', class_='search-result-product-url')['href']

    @classmethod
    def extract_name(cls, product, brand):
        line = product.get('Product Line', None)
        series = product.get('Series', product.get('Product Series', None))
        model = product.get('Model', None)
        name_parts = []
        name = ''
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
    def extract_form_factor(cls, product, type):
            if type == "desktop":
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
            elif type == "notebook":
                screen_size = product.get('Screen Size', None)
                if screen_size:
                    return int(float(screen_size.lower().replace('"', '').replace('inch','').strip()))
                else:
                    return "N/A"
            else:
                return "N/A"

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