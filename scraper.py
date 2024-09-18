from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import undetected_chromedriver as uc
import time
from datetime import datetime
from products import ProductManager, Product
from bs4 import BeautifulSoup
from hardware import HardwareManager, CPU, GPU
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

class WebScraper:
    def __init__(self, url):
        self.url = url

    def extract_product_info(self, products_html):
        """Extracts product details from the HTML using BeautifulSoup."""
        soup = BeautifulSoup(products_html, 'lxml')
        products = soup.find_all('li', class_='product list-view')
        for product in products:
            sku = self.extract_sku(product)
            price = self.extract_price(product)
            msrp = self.extract_msrp(product)
            stock = self.extract_stock(product)
            rebate = self.extract_rebate(product)
            sale = self.extract_sale(product)
            brand = self.extract_brand(product)
            url = self.extract_url(product)
            if "notebook" in url:
                type = "notebook"
            elif "desktop" in url:
                type = "desktop"
            updated = datetime.now().strftime("%m/%d/%Y")
            discovered = datetime.now().strftime("%m/%d/%Y")
            product_manager = ProductManager('sqlite:///products.db')
            product_manager.add_product(sku, stock, price, msrp, rebate, sale, brand, type, url, updated, discovered)

    @classmethod
    def extract_sku(cls, product):
        return product.find_all('div', class_='col-6')[0].find(text=True).strip() if product.find_all('div', class_='col-6')[0] else 'N/A'
    
    @classmethod
    def extract_stock(cls, product):
        return product.find_all('div', class_='col-6')[1].find(text=True).strip().replace('Stock: ', '').replace(',', '') if product.find_all('div', class_='col-6')[1] else 0

    @classmethod
    def extract_price(cls, product):
        return product.find('div', class_='col amount-list').find(text=True).strip().replace('$', '') if product.find('div', class_='col amount-list') else 0

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
        return product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.brand:' in text).find_next(text=True).strip() if product.find('div', style="background-color:#ddd; display:none;").find(text=lambda text: 'item.brand:' in text) else 0

    @classmethod
    def extract_url(cls, product):
        return product.find('div', class_='col-xs-12').find('a', href=True)['href']

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

    def scrape_hardware(self):
        """General scraping method to retrieve names and scores from the page."""
        options = uc.ChromeOptions() 
        options.headless = False
        driver = uc.Chrome(use_subprocess=True, options=options) 
        driver.get(self.url)

        # Wait for the table to appear
        item_table = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'cputable')))
        item_html = item_table.get_attribute("innerHTML")
        driver.close()
        
        # Parse the HTML
        soup = BeautifulSoup(item_html, 'lxml')
        hardware = soup.find('tbody').find_all('tr')

        for item in hardware:
            name = item.find('a').text if item.find('a') else None
            score = int(item.find_all('td')[1].text.replace(',', '')) if len(item.find_all('td')) > 1 else None
            
            if name and score:
                hardware_manager = HardwareManager('sqlite:///products.db')
                
                if 'cpu' in self.url:
                    hardware_manager.add_hardware(name, score, CPU)
                elif 'gpu' in self.url:
                    hardware_manager.add_hardware(name, score, GPU)

    def scrape_product_page(self):
        """Scrapes product data from a paginated website."""
        options = uc.ChromeOptions()
        options.headless = False
        driver = uc.Chrome(use_subprocess=True, options=options)
        driver.get(self.url)
        
        # Click on the top list button
        #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="list-btn-top"]'))).click()
        time.sleep(5)
        driver.find_element(By.XPATH, '//*[@id="list-btn-top"]').click()

        # Select 240 products per page
        #WebDriverWait(driver, 10).until( EC.presence_of_element_located((By.XPATH, '//*[@id="hits-per-page"]/div/select')))
        time.sleep(5)
        dropdown = Select(driver.find_element(By.XPATH, '//*[@id="hits-per-page"]/div/select'))
        dropdown.select_by_value("240")

        # Wait for the products to load
        #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "products")))
        time.sleep(2)
        container = driver.find_element(By.CLASS_NAME, "products")
        products_html = container.get_attribute("innerHTML")
        products_html = self.handle_pagination(driver, products_html)
        time.sleep(2)
        driver.quit()
        product_split = self.extract_product_info(products_html)

        return product_split

    def handle_pagination(self, driver, products_html):

        """Handles the pagination and concatenates product HTML."""
        try:
            #number_of_pages = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="pagination"]/div/ul')))
            number_of_pages = driver.find_element(By.XPATH, '//*[@id="pagination"]/div/ul')
            number_of_pages_html = number_of_pages.get_attribute("innerHTML")
            count_number_of_pages = number_of_pages_html.count('href')
            operation_count = 4

            while operation_count <= count_number_of_pages:
                page_xpath = '//*[@id="pagination"]/div/ul/li['+str(operation_count)+']/a'
                #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, page_xpath))).click()
                time.sleep(2)
                driver.find_element(By.XPATH, page_xpath).click() 
                # Wait for the products to load on the new page
                #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "products")))
                time.sleep(2)
                products = driver.find_element(By.CLASS_NAME, "products")
                products_html += products.get_attribute("innerHTML")
                operation_count += 1

        except Exception as e:
            pass
        
        return products_html
    
    def scrape_individual_products(self):
        print("Scraping individual products")
        engine = create_engine('sqlite:///products.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        products = session.query(Product).all()
        num_products = len(products)
        scanned_products = 0
        for product in products:
            print(f"Scanning product {scanned_products+1} of {num_products}")
            if product.scanned == False:
                try:
                    url = product.url
                    specs = {}
                    options = uc.ChromeOptions()
                    options.headless = False
                    driver = uc.Chrome(use_subprocess=True, options=options)
                    driver.get(url)
                    time.sleep(2)
                    container = driver.find_element(By.ID, 'tab-specification')
                    try:
                        products_html = container.get_attribute("innerHTML")
                        soup = BeautifulSoup(products_html, 'lxml')
                        spec = soup.find_all('tr')
                        for row in spec:
                            columns = row.find_all('td')
                            if len(columns) == 2:
                                label = columns[0].get_text(strip=True).replace(":", "")
                                value = columns[1].get_text(strip=True)
                                specs[label] = value
                        product.name = self.extract_name(specs, product.sku)
                        product.category = self.extract_category(specs)
                        if product.type == "notebook":
                            product.form_factor = self.extract_form_factor_notebook(specs)
                        if product.type == "desktop":
                            product.form_factor = self.extract_form_factor_desktop(specs)
                        product.cpu = self.extract_cpu(specs)
                        product.ram = self.extract_ram(specs)
                        product.ddr = self.extract_ddr(specs)
                        product.storage = self.extract_storage(specs)
                        product.os = self.extract_os(specs)
                        product.gpu = self.extract_gpu(specs)
                        product.touch = self.extract_touch(specs)
                        product.screen_res = self.extract_screen_res(specs)
                        product.screen_type = self.extract_screen_type(specs)
                        #product.screen_size = self.extract_screen_size(specs)
                        product.wifi = self.extract_wifi(specs)
                        product.keyboard = self.extract_keyboard(specs)
                        product.warranty = self.extract_warranty(specs)
                        product.warranty_desc = self.extract_warranty_desc(specs)
                        product.release_year = self.extract_release_year(specs)
                        product.scanned = True
                        time.sleep(2)
                        driver.quit()
                        session.commit()
                        scanned_products += 1
                    except:
                        driver.quit()
                        product.scanned = True
                        session.commit()
                except NoSuchElementException:
                    driver.quit()
                    products.append(product)
            else:
                scanned_products += 1
        session.close()
        print(f"Scanning product {scanned_products} of {num_products}")
        print("Scanning complete")
