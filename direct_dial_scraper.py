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


class DirectDialScraper:
    def __init__(self, url):
        self.url = url

    def scrape_product_page(self):
        print('Scraping product page')
        driver = self.setup_driver()
        self.navigate_to_page(driver)
        self.page_setup(driver)
        item = '.tab-content'
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

    def page_setup(self, driver):
        item = '.gridlist-view-button'
        self.wait_for_elements(driver, item, timeout=5)
        driver.find_element(By.XPATH, '//*[@id="list-btn-top"]').click()
        item = ".ais-HitsPerPage"
        self.wait_for_elements(driver, item, timeout=5)
        time.sleep(2)
        dropdown = Select(driver.find_element(By.XPATH, '//*[@id="hits-per-page"]/div/select'))
        dropdown.select_by_value("240")
        item = '.products'
        self.wait_for_elements(driver, item, timeout=5)
        time.sleep(2)

    def wait_for_elements(self, driver, item_class, timeout):
        wait = WebDriverWait(driver, timeout)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, item_class)))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, item_class)))

    def extract_html(self, driver):
        self.wait_for_elements(driver, '.tab-content', timeout=5)
        container = driver.find_element(By.CLASS_NAME, 'tab-content')
        return container.get_attribute("innerHTML")
    
    def extract_product_info(self, products_html):
        soup = BeautifulSoup(products_html, 'lxml')
        products = soup.find_all('li', class_="product list-view")
        products = [products[0]]
        for product in products:
            br_tags = product.find_all('br')
            for br in br_tags[5:]:
                if br.previous_sibling.get_text().strip() == '':
                    br_tags.remove(br)
            print(br_tags)
                #print(br.get_text())
            #print(sku)
            #price = self.extract_price(product)
            #msrp = self.extract_msrp(product)
            #stock = self.extract_stock(product)
            #rebate = self.extract_rebate(product)
            #sale = self.extract_sale(product)
            #brand = self.extract_brand(product)
            #url = self.extract_url(product)
            #updated = datetime.now().strftime("%m/%d/%Y")
            #discovered = datetime.now().strftime("%m/%d/%Y")
            #if "notebook" in self.url or "laptop" in self.url:
            #    type = "notebook"
            #elif "desktop" in self.url:
            #    type = "desktop"
            #elif 'workstation' in self.url:
            #    type = "workstation"
            #else:
            #    type = "N/A"
            #product_manager = ProductManager('sqlite:///direct_dial.db')
            #product_manager.add_direct_dial_product(sku, stock, price, msrp, rebate, sale, brand, type, url, updated, discovered)

    def scrape_individual_products(self):
        engine = create_engine('sqlite:///direct_dial.db')
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
        divs = product.find_all('div', class_='col-6')
        if divs and divs[0]:
            text = divs[0].get_text(strip=True)
            return text if text else 'N/A'
        else:
            return 'N/A'
    @classmethod
    def extract_rebate(cls, product):
        rebate_div = product.find('div', class_='in-stock item-alert w-100')
        if rebate_div:
            rebate_span = rebate_div.find('span', style="color:#333e48; font-weight:bold;")
            if rebate_span:
                rebate_text = rebate_span.find(text=True)
                if rebate_text:
                    return rebate_text.replace('$', '').strip()
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
        return product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.brand:' in text).find_next(text=True).strip() if product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.brand:' in text) else 0

    @classmethod
    def extract_url(cls, product):
        return "https://www.directdial.com"+product.find('div', class_='col-xs-12').find('a', href=True)['href']

    @classmethod
    def extract_name(cls, product, sku):
        line = product.get('Product Line', '')
        series = product.get('Product Series', '')
        model = product.get('Product Model', '')
        name = product.get('Product Name', '')
        final_name = ''
        final_name = final_name +line if line else final_name
        final_name = final_name + ' ' + series if series else final_name
        final_name = final_name + ' ' + model if model else final_name
        if sku in final_name:
            final_name = final_name.replace(sku, '').strip()
        if final_name != '':
            return final_name
        else:
            return "N/A"

    @classmethod
    def extract_category(cls, product):
         return f"{product.get('Product Type', None)}" if product.get('Product Type', None) else 'N/A'

    @classmethod
    def extract_form_factor_notebook(cls, product):
        screen_size = product.get('Screen Size', None)
        if screen_size:
            return int(float(screen_size.replace('"', '').strip()))
    
    @classmethod
    def extract_form_factor_desktop(cls, product):
        form_factor = product.get('Form Factor', "N/A").strip()
        form_factor_map = {
            "Desktop Mini": "Tiny",
            "Micro PC": "Tiny",
            "Tiny": "Tiny",
            "Mini PC": "Tiny",
            "Mini-tower": "SFF",
            "Small Form Factor": "SFF",
            "SFF": "SFF",
            "Ultra Small": "SFF",
            "Tower": "Tower",
            "Desktop": "All-in-One"
        }

        # Return the mapped value or "N/A" if form factor is not found
        return form_factor_map.get(form_factor, "N/A")

    @classmethod
    def extract_cpu(cls, product):
        processor_manufacturer = product.get('Processor Manufacturer', None)
        processor_type = product.get('Processor Type', None)
        processor_model = product.get('Processor Model', None)
        if processor_model.lower().startswith(processor_type.split()[-1].lower()):
            # Concatenate manufacturer and processor_model directly to avoid redundancy
            cpu = processor_manufacturer+" "+processor_type+processor_model[len(processor_type.split()[-1]):].strip()
        else:
            # Otherwise, concatenate all components
            cpu = processor_manufacturer+" "+processor_type+" "+processor_model
        return cpu

    @classmethod
    def extract_ram(cls, product):
        try:
            if "GB" in product.get('Total Installed System Memory').upper():
                return product.get('Total Installed System Memory').replace("GB", "").strip()
            else:
                return 0
        except:
            return 0

    @classmethod
    def extract_ddr(cls, product):
        ddr = product.get('System Memory Technology', 'N/A')
        if ddr == "N/A":
            if product.get('Graphics Memory Accessibility', "N/A") == "Shared":
                if product.get('Graphics Memory Technology', "N/A"):
                    ddr = product.get('Graphics Memory Technology', "N/A")
        if "DDR4" in ddr:
            return "DDR4"
        elif "DDR5" in ddr:
            return "DDR5"
        else:
            return "N/A"

    @classmethod
    def extract_storage(cls, product):
        storage = "N/A"
        if (product.get('Total Solid State Drive Capacity')):
            storage = product.get('Total Solid State Drive Capacity').upper()
        elif (product.get('Flash Memory Capacity')):
            storage = product.get('Flash Memory Capacity').upper()
        if storage != "N/A":
            if "GB" in storage:
                storage = int(storage.replace("GB", "").strip())
            elif "TB" in storage:
                storage = int(storage.replace("TB", "").strip())*1000
            return storage
        else:
            return 0

    @classmethod
    def extract_os(cls, product):
        return product.get('Operating System Platform', "N/A")

    @classmethod
    def extract_gpu(cls, product):
        graphics_controller_manufacturer = product.get('Graphics Controller Manufacturer', None)
        graphics_controller_model = product.get('Graphics Controller Model', None)
        graphics_memory_accessibility = product.get('Graphics Memory Accessibility', None)
        if graphics_memory_accessibility == "Shared":
            return "Integrated"
        elif graphics_memory_accessibility == "Dedicated":
            return graphics_controller_manufacturer+" "+graphics_controller_model
        elif "," in graphics_memory_accessibility:
            graphics_memory_accessibility = graphics_memory_accessibility.split(',')
            if graphics_memory_accessibility[0].strip() == "Dedicated":
                position = 0
            else:
                position = 1
            return graphics_controller_manufacturer.split(',')[position].strip()+" "+graphics_controller_model.split(',')[position].strip()

    @classmethod
    def extract_vram(cls, product):
        pass

    @classmethod
    def extract_screen_res(cls, product):
        return product.get('Screen Mode', "N/A")
    
    @classmethod
    def extract_screen_type(cls, product):
        return product.get('Display Screen Type', "N/A")
    
    @classmethod
    def extract_screen_size(cls, product):
        return product.get('Screen Size', "N/A")

    @classmethod
    def extract_wifi(cls, product):
        return product.get('Wireless LAN', "N/A")

    @classmethod
    def extract_keyboard(cls, product):
        return product.get('Keyboard Localization', "N/A")

    @classmethod
    def extract_touch(cls, product):
        return product.get('Touchscreen', "N/A")
        
    @classmethod
    def extract_ethernet(cls, product):
        return product.get('Ethernet Technology', "N/A") 

    @classmethod
    def extract_release_year(cls, product):
        return product.get('Release Year', "N/A")

    @classmethod
    def extract_warranty(cls, product):
        return product.get('Limited Warranty', "N/A")

    @classmethod    
    def extract_warranty_desc(cls, product):
        return product.get('Additional Warranty Information', "N/A")

    @classmethod
    def extract_type(cls, product):
        pass
    
    @classmethod
    def extract_stock(cls, product):
        return product.find_all('div', class_='col-6')[1].find(text=True).strip().replace('Stock: ', '').replace(',', '') if product.find_all('div', class_='col-6')[1] else 0

    @classmethod
    def extract_price(cls, product):
        return product.find('div', class_='col amount-list').find(text=True).strip().replace('$', '') if product.find('div', class_='col amount-list') else 0

    @classmethod
    def extract_msrp(cls, product):
        return product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.msrp:' in text).find_next(text=True).strip() if product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.msrp:' in text) else 0

