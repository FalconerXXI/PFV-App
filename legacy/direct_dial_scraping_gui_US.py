import urllib.parse
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import undetected_chromedriver as uc
import time
from datetime import datetime
import os
import re
from difflib import get_close_matches
import customtkinter
import threading
import queue

#scrape the website and return the html of the products
def scrape_website(url):
    msg_queue.put("STEP 1: Scraping Product Page for SKU, PRICE and STOCK\n")
    time.sleep(1)
    msg_queue.put("   Scanning Page 1\n")
    options = uc.ChromeOptions() 
    options.headless = False
    driver = uc.Chrome(use_subprocess=True, options=options) 
    driver.get(url)
    driver.set_window_size(1050, 750) 
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="list-btn-top"]').click()
    time.sleep(2)
    dropdown = Select(driver.find_element(By.XPATH, '//*[@id="hits-per-page"]/div/select'))
    dropdown.select_by_value("240")
    time.sleep(2)
    container = driver.find_element(By.CLASS_NAME, "products")
    products_html = container.get_attribute("innerHTML")
    time.sleep(2)
    number_of_pages = driver.find_element(By.XPATH, '//*[@id="pagination"]/div/ul')
    number_of_pages_html = number_of_pages.get_attribute("innerHTML")
    count_number_of_pages = number_of_pages_html.count('href')
    operation_count = 4
    if count_number_of_pages >= 4:
        while operation_count <= count_number_of_pages:
            msg_queue.put("   Scanning Page "+str(operation_count-2)+"\n")
            page_xpath = '//*[@id="pagination"]/div/ul/li['+str(operation_count)+']/a'
            driver.find_element(By.XPATH, page_xpath).click()
            time.sleep(2)    
            products = driver.find_element(By.CLASS_NAME, "products")
            products_html = products_html+products.get_attribute("innerHTML")
            operation_count = operation_count +1

    driver.close()
    cleaned_list = [line.strip() for line in products_html.splitlines()]
    msg_queue.put("STEP 1 COMPLETED: Scraped Product Pages\n\n")
    return(cleaned_list)

# Extracts the value of an attribute from a string between two strings
def extract_attribute_value(original_string, start_string, end_string):
    start_index = 0
    end_index = 0
    start_index = original_string.find(start_string)+len(start_string)
    end_index = original_string[start_index:].find(end_string)+start_index
    return original_string[start_index:end_index]

# Extracts the product information from the html product description
def format_product_info(product_description,category):
    product = [" "] * 41
    ## PRODUCT NUMBER
    product[0] = urllib.parse.unquote(extract_attribute_value(product_description, 'data-item-num="','" '))
    ## STOCK
    product[1] = extract_attribute_value(product_description, 'Stock: ','</p>').replace(",","")
    ## PRICE
    product[2] = extract_attribute_value(product_description, 'data-item-price="','" ')
    ## REEBATE
    if "Rebate" in product_description: 
        product[3] =  extract_attribute_value(product_description, 'showIR(item):<br><span style="color:#333e48; font-weight:bold;">$','</span>')
    else:
         product[3] = 0
    ## ADVERTISED SALE
    if "showSale(item.price, item.msrp):<br>Save $" in product_description:
        product[4] =  extract_attribute_value(product_description, 'showSale(item.price, item.msrp):<br>Save $','<br')
        if product[4] == ('K'):
            product[4] = int(product[4])*1000
    else:
         product[4] = 0
    ##URL
    product[26] ="http"+extract_attribute_value(product_description, '<a href="http','">')
    ##DATE UPDATED
    product[27] = datetime.now().strftime("%m/%d/%Y")
    product[30] = category
    return product 

#Converts all details of an elment to a string and adds them to a list of products
def extract_product_info(products,category):
    list_of_products = []
    product_description = ''
    for line in products:
        if line.startswith('<li class="product list-view">'):

            list_of_products.append(format_product_info(product_description, category))
            product_description=''
        else:
            product_description = product_description+line
    #removes first occurance of <li class>
    list_of_products.append(format_product_info(product_description, category))
    list_of_products.pop(0)
    return list_of_products

#Open CSV file and generate list of list 
def read_csv_to_list_of_lists(csv_file):
    msg_queue.put("STEP 2: Analyse Local Database\n")
    result = []
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                result.append(row)
    if len(result) > 1:
        msg_queue.put("STEP 2 COMPLETE: Local Database found and analysed\n\n")
        return result[1:]
    else:
        msg_queue.put("STEP 2 FAILED: Local Database NOT found and will now recreate database from scratch\n\n")
        return result

#Checks if the product from the website is already in the local list of products
def checks_if_web_in_local(web_row, local_products):
    current_date = datetime.now().strftime("%m/%d/%Y")
    for index_local, local_row in enumerate(local_products):
        if local_row[0] == web_row[0]:
            local_row[27] = current_date
            # If the web product has changed, update the local product
            if local_row != web_row:
                local_products[index_local][1] = web_row[1]
                local_products[index_local][2] = web_row[2]
                local_products[index_local][3] = web_row[3]
                local_products[index_local][4] = web_row[4]
                local_products[index_local][26] = web_row[26] 
                for index_web, x in enumerate(local_row):
                    if ((x == ' ' and x == 'Not Specified') and (web_row[index_web] != ' ' and web_row[index_web] != 'Not Specified')):
                        local_products[index_local][index_web] = web_row[index_web]      
            return local_products
    web_row[27] = current_date
    local_products.append(web_row)
    return local_products

#Compare updated info from website and current info in CSV
def compare_web_to_csv(web_products, local_products):
    if len(local_products) <= 2:
        return web_products
    else:
        for web_row in web_products:
            local_products = checks_if_web_in_local(web_row,local_products)
    return local_products

#Get the specifications of the product
def specification_scrape(updated_products):
    retries_count = 0
    for index, product in enumerate(updated_products):
        try:
            msg_queue.put("    Scanning product: "+ str(index+1) + " of " + str(len(updated_products))+"\n")
            new_product = [' '] *41
            options = uc.ChromeOptions() 
            options.headless = False
            driver = uc.Chrome(use_subprocess=True, options=options) 
            driver.get(product[26])
            driver.set_window_size(1050, 750) 
            time.sleep(2)
            container = driver.find_element(By.ID, 'tab-specification') 
            products_html = container.get_attribute("innerHTML").splitlines()
            cleaned_list = [line.strip() for line in products_html]
            cpu_brand = ''
            cpu_type = ''
            cpu_model = ''
            html_list = [(0,'<td>Manufacturer Part Number:</td>'), (5,'<td>Brand Name:</td>'), (9,'<td>Total Installed System Memory:</td>'), (9,'<td>Standard Memory:</td>'), (7,'<td>Form Factor:</td>'), (7,'<td>Screen Size:</td>'), (10,'<td>System Memory Technology:</td>'), (10, '<td>On-board Memory Technology:</td>'), (10, '<td>Memory Technology:</td>'), (11,'<td>Total Solid State Drive Capacity:</td>'), (11, '<td>Flash Memory Capacity:</td>'), (12,'<td>Operating System:</td>'), (15,'<td>Screen Mode:</td>'), (16,'<td>Display Screen Type:</td>'), (16, '<td>Display Screen Technology:</td>'), (17,'<td>Wireless LAN:</td>'), (18,'<td>Keyboard Localization:</td>'), (19,'<td>Touchscreen:</td>'), (20,'<td>Ethernet Technology:</td>'), (21,'<td>Release Year:</td>'), (22,'<td>Limited Warranty:</td>'),(23,'<td>Additional Warranty Information:</td>'), (24,'<td>Product Type:</td>')]
            for item in html_list:
                if item[1] in cleaned_list:
                    if  new_product[item[0]] == " " or new_product[item[0]] == "Not Specified":
                        new_product[item[0]] = re.sub('<.*?>', '',cleaned_list[cleaned_list.index(item[1])+1][4:]).strip()
                else:
                    if  new_product[item[0]] == " " or new_product[item[0]] == "Not Specified":
                        new_product[item[0]] = "Not Specified"
            if new_product[5].lower() == 'hp':
                new_product[5] = new_product[5].upper()
            else:
                new_product[5] = new_product[5].title() 

            ## Clean up name
            product_line = ''
            product_series = ''
            product_model = ''
            if '<td>Product Line:</td>' in cleaned_list:
                product_line = cleaned_list[cleaned_list.index('<td>Product Line:</td>')+1][4:].strip()
            if '<td>Product Series:</td>' in cleaned_list:
                product_series = cleaned_list[cleaned_list.index('<td>Product Series:</td>')+1][4:].strip()
            if '<td>Product Model:</td>' in cleaned_list:
                product_model = cleaned_list[cleaned_list.index('<td>Product Model:</td>')+1][4:].strip()
            new_product[6] = product_line + ' ' + product_series + ' ' + product_model
            if ' ' +new_product[0] in new_product[6]:
                new_product[6] = new_product[6].replace(' ' +new_product[0], '').strip()

            ## Function to convert ssd from TB to GB
            if "TB" in new_product[11]: 
                new_product[11] = str(int(new_product[11][0])*1000) + " GB"

            ## FORM FACTOR
            if new_product[7] != ' ':
                if '"' in new_product[7]:
                    new_product[7] = new_product[7].replace('"', '').strip()
                    new_product[7] = str(round(float(new_product[7])))
                elif (new_product[7] == "Desktop Mini" or new_product[7] == "Micro PC" or new_product[7] == "Tiny" or new_product[7] == "Mini PC" ):
                    new_product[7] = "Tiny"
                elif (new_product[7] == "Mini-tower" or new_product[7] == "Small Form Factor" or new_product[7] == "SFF" or new_product[7] == "Ultra Small"):
                    new_product[7] = "Mini-Tower"
                elif new_product[7] == "Tower":
                    product[7] = "Tower"
                elif new_product[7] == "Desktop":
                    product[7] = "All-in-One"
                else:
                    new_product[7] = "Not Specified"
            else:
                new_product[7] = "Not Specified"


        

            ##CLEAN UP VRAM
            if "Up to " in new_product[14]:
                new_product[14] = new_product[14].replace("Up to ", "").strip()
            
            ##CPU INFO
            if '<td>Processor Manufacturer:</td>' in cleaned_list:
                cpu_brand = cleaned_list[cleaned_list.index('<td>Processor Manufacturer:</td>')+1][4:].strip()
            if '<td>Processor Type:</td>' in cleaned_list:
                cpu_type = cleaned_list[cleaned_list.index('<td>Processor Type:</td>')+1][4:].strip()
            if '<td>Processor Model:</td>' in cleaned_list:
                cpu_model = cleaned_list[cleaned_list.index('<td>Processor Model:</td>')+1][4:].strip()
            if (cpu_brand != '' and cpu_type != '' and cpu_model != ''):
                overlap_length = 0
                max_overlap = min(len(cpu_type), len(cpu_model))
                for i in range(max_overlap +1):
                    if cpu_type.lower()[-i:] == cpu_model.lower()[:i]:
                        overlap_length = i
                if overlap_length > 1:
                    new_product[8] = cpu_brand + ' ' + cpu_type[:-overlap_length]+cpu_model
                else:   
                    new_product[8] = cpu_brand + ' ' + cpu_type + ' ' + cpu_model
            else:
                new_product[8] = "Not Specified"
            
            ##GPU  INFO 
            if '<td>Graphics Memory Accessibility:</td>' in cleaned_list:
                if '<td>Graphics Controller Model:</td>' in cleaned_list:
                    gpu_type = cleaned_list[cleaned_list.index('<td>Graphics Memory Accessibility:</td>')+1][4:]
                    if "," in cleaned_list[cleaned_list.index('<td>Graphics Memory Accessibility:</td>')+1][4:]:
                        gpu_type_split = gpu_type.split(',')
                        for i in range(len(gpu_type_split)):
                            if "Dedicated" in gpu_type_split[i]:
                                if "<td>Graphics Controller Manufacturer:</td>" in cleaned_list:
                                    if "," in cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:]:
                                        if "," in cleaned_list[cleaned_list.index('<td>Graphics Controller Manufacturer:</td>')+1][4:]:
                                            new_product[13] = cleaned_list[cleaned_list.index('<td>Graphics Controller Manufacturer:</td>')+1][4:].split(',')[i].strip() + " " + cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:].split(',')[i].strip()
                                        else:
                                            new_product[13] = cleaned_list[cleaned_list.index('<td>Graphics Controller Manufacturer:</td>')+1][4:].strip() + " " + cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:].split(',')[i].strip()
                                    else:
                                        if "," in cleaned_list[cleaned_list.index('<td>Graphics Controller Manufacturer:</td>')+1][4:]:
                                            new_product[13] = cleaned_list[cleaned_list.index('<td>Graphics Controller Manufacturer:</td>')+1][4:].split(',')[i].strip() + " " + cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:].strip()
                                        else:
                                            new_product[13] = cleaned_list[cleaned_list.index('<td>Graphics Controller Manufacturer:</td>')+1][4:].strip() + " " + cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:].split(',')
                                else:
                                    new_product[13] = cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:].split(',')[i].strip()
                                if '<td>Graphics Memory Capacity:</td>' in cleaned_list:
                                    new_product[14] = cleaned_list[cleaned_list.index('<td>Graphics Memory Capacity:</td>')+1][4:]
                                else:
                                    new_product[14] = "Not Specified"
                        if new_product[13] == " " and new_product[14] == " ":
                            new_product[13] = "Integrated"
                            new_product[14] = "0 GB"
                    else:
                        if "Dedicated" in cleaned_list[cleaned_list.index('<td>Graphics Memory Accessibility:</td>')+1][4:]:
                            if "<td>Graphics Controller Manufacturer:</td>" in cleaned_list:
                                new_product[13] = cleaned_list[cleaned_list.index('<td>Graphics Controller Manufacturer:</td>')+1][4:].strip() + " " + cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:].strip()
                            else:
                                new_product[13] = cleaned_list[cleaned_list.index('<td>Graphics Controller Model:</td>')+1][4:].strip()
                            if '<td>Graphics Memory Capacity:</td>' in cleaned_list:
                                new_product[14] = cleaned_list[cleaned_list.index('<td>Graphics Memory Capacity:</td>')+1][4:]
                            else:
                                new_product[14] = "Not Specified"
                        else:
                            new_product[13] = "Integrated"
                            new_product[14] = "0 GB"
                else:
                    new_product[13] = "Integrated"
                    new_product[14] = "0 GB"
            else:
                new_product[13] = "Not Specified"
                new_product[14] = "Not Specified"

            ##CLEAN UP GPU NAME FOR LAPTOPS
            if new_product[13].lower().endswith("ada"):
                new_product[13] = new_product[13]+" Generation"
            
            if new_product[24] in ['Notebook', 'Ultrabook', 'Gaming Notebook', '2 in 1 Notebook', '2 in 1 Chromebook', '2 in 1 Ultrabook', 'Thin Client Notebook', 'Netbook', 'Chromebook', 'Mobile Workstation']:
                if "NVIDIA" in new_product[13]:
                    new_product[13] = new_product[13] + " Laptop GPU"
            if "Quadro" in new_product[13]:
                new_product[13] = new_product[13].replace("Quadro ", "")
            if "Graphics " in new_product[13]:
                new_product[13] = new_product[13].replace("Graphics ", "")

            ##CLEAN UP SCREEN TYPE
            if 'ips' in new_product[16].lower():
                new_product[16] = "IPS"
            if 'lcd' in new_product[16].lower():
                new_product[16] = "LCD"
            if 'oled' in new_product[16].lower():
                new_product[16] = "OLED"
            elif 'led' in new_product[16].lower():
                new_product[16] = "LED"
            if 'tn' in new_product[16].lower():
                new_product[16] = "TN"


            ##CLEAN UP DDR TYPE
            if new_product[10] == "Not Specified" and new_product[13] == "Integrated":
                if '<td>Graphics Memory Technology:</td>' in cleaned_list:
                    new_product[10] = re.sub('<.*?>', '',cleaned_list[cleaned_list.index('<td>Graphics Memory Technology:</td>')+1][4:]).strip()

            if "ddr4" in new_product[10].lower():
                new_product[10] = "DDR4"
            elif "ddr5" in new_product[10].lower():
                new_product[10] = "DDR5"
            else:
                new_product[10] = "Not Specified"

            ##Success 
            new_product[28] = "TRUE"
        
            msg_queue.put("     Product: "+ str(index+1) + " scanned successfully\n")
            msg_queue.put("     Remaning retries: "+ str(retries_count)+"\n")
        except NoSuchElementException:
            new_product[28] = "FALSE"
            retries_count = retries_count+1
            msg_queue.put("     Product: "+ str(index+1) + " scanned unsuccessfully\n")
            msg_queue.put("     Remaning retries: "+ str(retries_count)+"\n")
        updated_product = []
        for index_2, item in enumerate(new_product):
            if (item !=" " and  (product[index_2] == " " or product[index_2] =="FALSE")):
                updated_product.append(new_product[index_2])
            else:
                updated_product.append(product[index_2])
        time.sleep(.5)
        driver.close()
        updated_products[index] = updated_product
    return(updated_products)

def run_specification_scrape(updated_products):
    msg_queue.put("STEP 3: Scanning Individual MTMs\n")
    unfinished_products = updated_products
    finished_products = []
    while len(unfinished_products) > 0:
        index = 0
        while index < len(unfinished_products):
            if unfinished_products[index][28] == "TRUE":
                finished_products.append(unfinished_products.pop(index))
            else:
                index += 1
        unfinished_products = specification_scrape(unfinished_products)
    msg_queue.put("STEP 3 COMPLETED: Scanning Individual MTMs\n\n")
    return finished_products

# Checks if all fields are filled in
def check_missing_fields(updated_products):
    msg_queue.put("STEP 4: Checking For Missing Feilds\n")
    for index, product in enumerate(updated_products):
        if "Not Specified" in product[:15]:
            updated_products[index][29] = "TRUE"
        else:
            updated_products[index][29] = "FALSE"
        for itme in product[:15]:
            if itme == " ":
                updated_products[index][29] = "TRUE"
    msg_queue.put("STEP 4 COMPLETED: Missing Feilds Identified\n\n")
    return updated_products

# Sorts the list of products based on the stock
def sort_by_stock(lists):
    #return lists
    return sorted(lists, key=lambda x: int(x[1]), reverse=True)

# Function to compute scores
def compute_score(products, cpu_scores, gpu_scores, form_factor_weights, category):
    """
    Computes the scores for a list of products based on their attributes and weights.

    Args:
        products (list): A list of products, where each product is a list of attributes.
        cpu_scores (list): A list of CPU scores, where each score is a list of CPU name and score.
        gpu_scores (list): A list of GPU scores, where each score is a list of GPU name and score.

    Returns:
        list: A list of results, where each result is a list of SKU and score.

    """
    msg_queue.put("STEP 6: Compute MTMs Scores\n")
    def normalize(value, min_value, max_value):
        return (value - min_value) / (max_value - min_value) if max_value > min_value else 0

    def get_cpu_score(cpu_name):
        if cpu_name == "Not Specified":
            return 0
        if cpu_name == " ": 
            return 0
        if cpu_name == "": 
            return 0
        for cpu_index, cpu in enumerate(cpu_scores):
            if '@' in cpu[0]:
                cpu_scores[cpu_index] = (cpu[0].split('@')[0], cpu[1])
                
        for cpu in cpu_scores:
            if cpu[0] == cpu_name:
                return cpu[1]
        msg_queue.put("    CPU not found: " + cpu_name+ "\n")
        time.sleep(.5)
        closest = get_close_matches(cpu_name, [cpu[0] for cpu in cpu_scores], n=1)
        if closest:
            
            for cpu in cpu_scores:
                if cpu[0] == closest[0]:
                    msg_queue.put("    Match found: " + closest[0]+"\n\n")
                    time.sleep(.2)
                    return cpu[1] 
        return 0

    def get_gpu_score(gpu_name, gpu_memory):
        gpu_name2 = gpu_name.lower()
        if gpu_name2 == "not specified":
            return 0
        if gpu_name2 == "integrated":
            return 0
        if gpu_name2 == '':
            return 0
        if gpu_name2 == ' ':
            return 0
        for gpu in gpu_scores:
            first, _, rest = gpu_name2.partition(" ")
            gpu_backup = rest or first
            gpu_backup_2 = gpu_name2+" " + gpu_memory
            gpu_backup_5 = gpu_name2+ " " +gpu_memory.replace(' ', '')
            first2, _, rest2 = gpu_backup_2.partition(" ")
            gpu_backup_3 = rest2 or first2
            gpu_backup_4 = gpu_backup_2.lower()
            gpu_backup_4 = gpu_backup_4.replace('nvidia ', '').replace('geforce ', '').replace('quadro ', '').strip()
            gpu_backup_5 = gpu_backup_5.lower()
            gpu_backup_5 = gpu_backup_5.replace('nvidia ', '').replace('geforce ', '').replace('quadro ', '').strip()
            
            gpu_score_name = gpu[0].lower()
            if "nvidia " in gpu_name2:
                gpu_name2 = gpu_name2.replace("nvidia ", "")
            if "intel " in gpu_name2:
                gpu_name2 = gpu_name2.replace("intel ", "")
            if 'geforce ' in gpu_name2:
                gpu_name2 = gpu_name2.replace('geforce ', '')
            if 'graphics' in gpu_name2:
                gpu_name2 = gpu_name2.replace('graphics', '')
            if 'nvidia ' in gpu_score_name:
                gpu_score_name = gpu_score_name.replace('nvidia ', '')
            if 'geforce ' in gpu_score_name:
                gpu_score_name = gpu_score_name.replace('geforce ', '')
            if 'intel ' in gpu_score_name:
                gpu_score_name = gpu_score_name.replace('intel ', '')
            if 'graphics' in gpu_score_name:
                gpu_score_name = gpu_score_name.replace('graphics', '')
            gpu_compare = gpu[0].lower()
            if gpu[0].lower() == gpu_name2.lower():
                return gpu[1]
            elif gpu[0].lower() == gpu_backup.lower():
                return gpu[1]
            if gpu[0].lower() == gpu_backup_2.lower():
                return gpu[1]
            if gpu_compare.replace('nvidia ', '').replace('geforce ', '').replace('quadro ', '') == gpu_backup_4.lower():
                return gpu[1]
            if gpu_compare.replace('nvidia ', '').replace('geforce ', '').replace('quadro ', '') == gpu_backup_5.lower():
                return gpu[1]
            if gpu[0].lower() == gpu_backup_3.lower():
                return gpu[1]
            if gpu[0].lower().replace('nvidia ', '').replace('geforce ', '').replace('quadro ', '') == gpu_backup_3.lower().replace('nvidia ', '').replace('geforce ', '').replace('quadro ', ''):
                return gpu[1]
        msg_queue.put("    GPU not found: " + gpu_name+"\n")
        updated_gpu_list = [(gpu[0].lower().replace('nvidia ', '').replace('geforce ', '').replace('quadro ', ''), gpu[1]) for gpu in gpu_scores]
        pattern = r'\b([A-Za-z]*\d+)\b'
        matches = re.findall(pattern, gpu_name2, re.IGNORECASE)
        if matches:
            matche = matches[0]
        else:
            matche = gpu_name2
        updated_gpu_list_more = []
        for gpu_parse in updated_gpu_list:
            if re.search(rf'\b{matche}\b', gpu_parse[0]):
                updated_gpu_list_more.append(gpu_parse)
        if len(updated_gpu_list_more) == 0:
            updated_gpu_list_more = updated_gpu_list
        time.sleep(.5)
        closest = get_close_matches(gpu_name2, [gpu[0] for gpu in updated_gpu_list_more], n=1)
        if closest:
    
            for index, gpu in enumerate(updated_gpu_list):
                if gpu[0].lower() == closest[0].lower():
                    msg_queue.put("    Match found: " + gpu_scores[index][0]+"\n\n")
                    return gpu_scores[index][1]
        return 0

    for index, product in enumerate(products):
        try:
            ##WEIGHTS
            weights = {
                'form_factor': 0.5,
                'cpu': 0.499,
                'ram': 0.00025,
                'storage': 0.00025,
                'gpu': 0.0005,
            }
            ##CPU SCORE
            if product[8] != "Not Specified":
                normalized_cpu = normalize(get_cpu_score(product[8]), min([cpu[1] for cpu in cpu_scores]), max([cpu[1] for cpu in cpu_scores]))
            else:
                normalized_cpu = 0
            if product[8] != "Not Specified":
                normalized_form_factor = form_factor_weights.get(product[7], 0)
            else:
                normalized_form_factor = 0
            if product[9] != "Not Specified":
                normalized_ram = normalize(int(product[9].replace(' GB', '')), 4, 128) 
            else:
                normalized_ram = 0
            if product[11] != "Not Specified":
                normalized_storage = normalize(int(product[11].replace(' GB', '')), 0, 2000)
            else:
                normalized_storage = 0
            if product[13] != "Not Specified":
                normalized_gpu = normalize(get_gpu_score(product[13], product[14]), min([gpu[1] for gpu in gpu_scores]), max([gpu[1] for gpu in gpu_scores]))
            else:
                normalized_gpu = 0
            # Calculate score
            score = (weights['form_factor'] * normalized_form_factor + weights['cpu'] * normalized_cpu + weights['ram'] * normalized_ram + weights['storage'] * normalized_storage + weights['gpu'] * normalized_gpu)


            
        except ValueError:
            score = 0
        if product[30] == category:
            products[index][25] = score*1000
    msg_queue.put("STEP 6 COMPLETED: Computed Scores\n\n")
    time.sleep(1)
    return products

# Function to scrape scores from a URL
def scrape_score(url):
    """
    Scrapes the scores from a given URL and returns a list of tuples containing the name and its score.

    Args:
        url (str): The URL of the webpage containing the scores.

    Returns:
        list: A list of tuples containing the name and its score.
    """
    options = uc.ChromeOptions() 
    options.headless = False
    driver = uc.Chrome(use_subprocess=True, options=options) 
    driver.get(url)
    driver.set_window_size(1050, 750) 
    item_table = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'cputable')))
    item_html = item_table.get_attribute("innerHTML")
    item_list_html = item_html.split('<tr id=')[1:]
    scores = []
    for item in item_list_html:
        name = extract_attribute_value(item, '">', '</a></td><td>')
        score = int(extract_attribute_value(item, '</a></td><td>', '</td><td>').replace(',', ''))
        name = name[name.rfind('">') + 2:]
        scores.append((name, score))
    driver.close()
    return scores

# Function to get the closest competitors
def competitors(products):
    for index_product, product in enumerate(products):
        closest_skus = []
        closest_skus_dell = []
        closest_skus_hp = []
        closest_skus_lenovo = []
        for other_product in products:
            try:
                score_diffs = (other_product[0], float(abs(float(product[25]) - float(other_product[25]))))
            except ValueError:
                score_diffs = (other_product[0], 0)
            if product[30] == other_product[30]:
                if product[5] == 'Lenovo' and other_product[5] == 'HP':
                    closest_skus_hp.append(score_diffs)
                if product[5] == 'Lenovo' and other_product[5] == 'Dell':
                    closest_skus_dell.append(score_diffs)
                if product[5] == 'HP' and other_product[5] == 'Lenovo':
                    closest_skus_lenovo.append(score_diffs)
                if product[5] == 'Dell' and other_product[5] == 'Lenovo':
                    closest_skus_lenovo.append(score_diffs)
                    
        if product[5] != 'Lenovo':
            closest_skus = sorted(closest_skus_lenovo, key=lambda x: float(x[1]))[:10]
        else:
            closest_skus_dell = sorted(closest_skus_dell, key=lambda x: float(x[1]))[:5]
            closest_skus_hp = sorted(closest_skus_hp, key=lambda x: float(x[1]))[:5]
            closest_skus = closest_skus_dell + closest_skus_hp

        
        for index_sku, sku in enumerate(closest_skus):
            products[index_product][index_sku+31] = sku[0]
    return products

# Function to add header
def add_header(sorted_products):
    header = ["SKU", "STOCK", "PRICE", "REEBATE", "SALE", "BRAND", "NAME", "FORM FACTOR", "CPU","RAM", "DDR", "STORAGE", "OS", "GPU", "VRAM", "SCREEN RES.","SCREEN TYPE", "WiFi", "KEYBOARD", "TOUCH", "ETHERNET", "RELEASE YEAR", "WARRANTY", "WARRANTY DESC.", "TYPE", "SCORE", "URL", "UPDATED", "SUCCESS", "FIX", "CATEGORY", "COMPETITOR 1", "COMPETITOR 2", "COMPETITOR 3", "COMPETITOR 4", "COMPETITOR 5", "COMPETITOR 6", "COMPETITOR 7", "COMPETITOR 8", "COMPETITOR 9", "COMPETITOR 10"]
    sorted_products.insert(0,header)
    return sorted_products

# Function to write to a CSV file
def write_csv(file, data):
    with open(file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

# Function to read a CSV file into a dictionary
def read_csv_to_dict(filename):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        # If the file doesn't exist or is empty, return an empty header and dictionary
        return [], {}
    
    with open(filename, mode='r', newline='') as file:
        reader = csv.reader(file)
        data = list(reader)
        
    header = data[0]
    data_dict = {row[0]: row[1:] for row in data[1:]}
    
    return header, data_dict

# Function to update the pricing dictionary
def update_pricing_dict(header, data_dict, new_data):
    msg_queue.put("STEP 6: Updating Price History\n")
    today = datetime.now().strftime('%m/%d/%Y')
    
    # If the header is empty (new or empty CSV), create the initial header
    if not header:
        header = ['SKU', today]
    
    # Insert the new date at index 1 if it's not already there
    
    skus_in_csv = set(data_dict.keys())
    skus_in_new_data = set()
    
    for new_product in new_data[1:]:
        sku = new_product[0]
        new_price = new_product[2].replace('$', '').replace(',', '')
        new_date = new_date = datetime.strptime(new_product[27], '%m/%d/%Y').strftime('%m/%d/%Y')
        skus_in_new_data.add(sku)
        
        if new_date != today:
            new_price = '0'
        
        if sku in data_dict:
            # Insert the new price at index 1 for the existing SKU
            if today != datetime.strptime(header[1], '%m/%d/%Y').strftime('%m/%d/%Y'):
                data_dict[sku].insert(0, new_price)
            else:
                data_dict[sku][0]= new_price
        else:
            # Create a new entry for the new SKU
            data_dict[sku] = [new_price] + ['$0'] * (len(header) - 2)
    
    # For SKUs in the CSV that are not in the new data, set today's price to $0
    
    if today != datetime.strptime(header[1], '%m/%d/%Y').strftime('%m/%d/%Y'):
        header.insert(1, today)
        
    for sku in skus_in_csv - skus_in_new_data:
        data_dict[sku].insert(0, '$0')
    msg_queue.put("STEP 6 COMPLETED: Updated Price History\n")
    return header, data_dict

# Function to update the stock dictionary
def update_stock_dict(header, data_dict, new_data):
    msg_queue.put("STEP 7: Updating Stock History\n")
    today = datetime.now().strftime('%m/%d/%Y')
    
    # If the header is empty (new or empty CSV), create the initial header
    if not header:
        header = ['SKU', today]
    
    # Insert the new date at index 1 if it's not already there
    
    skus_in_csv = set(data_dict.keys())
    skus_in_new_data = set()
    
    for new_product in new_data[1:]:
        sku = new_product[0]
        new_stock = new_product[1]
        new_date = new_date = datetime.strptime(new_product[27], '%m/%d/%Y').strftime('%m/%d/%Y')
        skus_in_new_data.add(sku)
        
        if new_date != today:
            new_stock = '0'
        
        if sku in data_dict:
            # Insert the new price at index 1 for the existing SKU
            if today != datetime.strptime(header[1], '%m/%d/%Y').strftime('%m/%d/%Y'):
                data_dict[sku].insert(0, new_stock)
            else:
                data_dict[sku][0]= new_stock
        else:
            # Create a new entry for the new SKU
            data_dict[sku] = [new_stock] + ['0'] * (len(header) - 2)
    
    # For SKUs in the CSV that are not in the new data, set today's price to $0
    
    if today != datetime.strptime(header[1], '%m/%d/%Y').strftime('%m/%d/%Y'):
        header.insert(1, today)
        
    for sku in skus_in_csv - skus_in_new_data:
        data_dict[sku].insert(0, '0')
    msg_queue.put("STEP 7 COMPLETED:  Updated Stock History\n")
    return header, data_dict


# Function to save a dictionary to a CSV file
def save_dict_to_csv(header, data_dict, filename):
    msg_queue.put("STEP 8: Saving Scraped Data to the Database\n")
    time.sleep(2)
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        
        for sku, prices in data_dict.items():
            writer.writerow([sku] + prices)
    msg_queue.put("STEP 8 COMPLETE: Saved Scraped Data to the Database***\n")
    time.sleep(.5)

""" ----------------- MAIN ----------------- """

def check_all_fields(products,error_csv):
    error_csv_list = read_csv_to_list_of_lists(error_csv)
    msg_queue.put("STEP 4: Check For Errors in Data\n")
    header = products[0]
    index_to_check = [6, 5, 7, 8, 9, 11, 13]
    error_count = 0
    for product_index, product in enumerate(products[1:]):
        error_message = ""
        errors = []
        for item_index, item in enumerate(product):
            if item_index in index_to_check:
                if item == " " or item == "Not Specified":
                    errors.append(header[item_index])

        if len(errors) > 1:   
            for er in errors[:-1]:
                error_message = error_message + str(er) + ", "
            error_message = error_message + "and "+str(errors[len(errors)-1])
        elif len(errors) > 0:
            error_message = str(errors[0])
        if error_message != "":
            if product[5]== "Lenovo" or product[5] == "Not Specified":
                x = False
                for sublist in error_csv_list:
                    if product[0] in sublist:
                        x = True
                if x == False:
                    error_csv_list.append([product[30], product[0], error_message, product[26] ])
            error_message = "   Data Error: "+str(product[0])+ "   Row: "+ str(product_index+2)+"\n"
            error_count = error_count + 1
            msg_queue.put(error_message)
            time.sleep(1)
    if len(error_csv_list) == 0:
        error_csv_list.append(["CATEGORY","SKU", "ERROR", "URL"])
    elif error_csv_list[0] != ["CATEGORY","SKU", "ERROR", "URL"]:
        error_csv_list.insert(0, ["CATEGORY","SKU", "ERROR", "URL"])
    write_csv(error_csv, error_csv_list)
    msg_queue.put("Total Errors: "+str(error_count)+"\n")
    msg_queue.put("STEP 4 COMPLETED: Errors Identified and Reported\n")

def adjust_score_out_of_stock(products):
    for product in products:
        if product[27] != datetime.now().strftime('%m/%d/%Y'):
            product[1] = "0"
            product[25] = 0
    return products

##### Building the list of lists of products

#scrape the website
def pfv_function(url, spec_csv, price_csv, stock_csv, ff_weights,error_csv, category):
    scraped_contents = scrape_website(url)
    #extract the product information
    web_products = extract_product_info(scraped_contents, category)

    #read the csv file
    local_products = read_csv_to_list_of_lists(spec_csv)

    #compare the updated info from the website and the current info in the CSV
    updated_products = compare_web_to_csv(web_products, local_products)

    #scrape the specifications of the products and update the list of products

    checked_products = run_specification_scrape(updated_products)

    #check if all fields are filled in
    checked = check_missing_fields(checked_products)

    #sort the list of products based on the stock
    sorted_products = sort_by_stock(checked)

    ####### Computing the scores of the products

    #get the cpu scores
    time.sleep(1)
    cpu_scores = scrape_score('https://www.cpubenchmark.net/cpu_list.php')

    #get the gpu scores
    gpu_scores = scrape_score('https://www.videocardbenchmark.net/gpu_list.php')

    #Compute the product scores
    scored = compute_score(sorted_products, cpu_scores, gpu_scores, ff_weights, category)

    #Get the closest competitors


    adjusted_products = adjust_score_out_of_stock(scored)
    closest_competitors = competitors(adjusted_products)

    #Add header
    final_products = add_header(closest_competitors)


    ##### Writing the final list of products to a CSV file

    #write to csv
    write_csv(spec_csv, closest_competitors)

    check_all_fields(final_products,error_csv)
    ##### Price Tracking

    #Read existing data into dictionary
    header, data_dict = read_csv_to_dict(price_csv)

    #Update the pricing dictionary with new data
    header, updated_data_dict = update_pricing_dict(header, data_dict, final_products)

    save_dict_to_csv(header, updated_data_dict, price_csv)

    header, data_dict = read_csv_to_dict(stock_csv)

    header, updated_data_dict = update_stock_dict(header, data_dict, final_products)
    save_dict_to_csv(header, updated_data_dict, stock_csv)


    #Save the updated pricing dictionary to a CSV file
    msg_queue.put("STEP 7: Saving Scraped Data to the Database\n")
    time.sleep(2)
    msg_queue.put("STEP 7 COMPLETE: Saved Scraped Data to the Database***\n")
    msg_queue.put("------Process Completed------\n")

def run_pfv(list_par):
    thread = threading.Thread(target=pfv_inter, args=(list_par,))
    if threading.active_count() > 1:
        thread.join()
    else:
        thread.start()
    
def pfv_inter(list_par):
    for i in list_par:
        url = i[0]
        spec_csv = i[1]
        price_csv = i[2]
        stock_csv = i[3]
        ff_weights = i[4]
        errors_csv = i[5]  
        category = i[6] 
        pfv_function(url, spec_csv, price_csv, stock_csv, ff_weights, errors_csv, category)
    reset_buttons()

def Notebooks():
    textbox.configure(state="normal")
    textbox.insert("end", "Starting Notebooks data collection...\n")
    textbox.configure(state="disabled")
    button_notebooks.configure(state="disabled")
    button_desktops.configure(state="disabled")
    button_workstations.configure(state="disabled")
    button_mobile_workstations.configure(state="disabled")
    button_all.configure(state="disabled")
    button_cancel.configure(state="normal")
    list_par = []
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/notebooks/notebook?instock=true&productType=Notebook&brand=HP&brand=Dell&brand=Lenovo")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'12': 0.005, '13':0.05, '14': 0.8, '15': 0.3, '16': 0.6, '17': 0.4})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Notebook')
    list_par.append(list_par_tmp)
    run_pfv(list_par)

def Desktops():
    textbox.configure(state="normal")
    textbox.insert("end", "Starting Desktops data collection...\n")
    textbox.configure(state="disabled")
    button_notebooks.configure(state="disabled")
    button_desktops.configure(state="disabled")
    button_workstations.configure(state="disabled")
    button_mobile_workstations.configure(state="disabled")
    button_all.configure(state="disabled")
    button_cancel.configure(state="normal")
    list_par = []
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/desktop-computers?sortBy=stock%3Adesc&instock=true&brand=Lenovo&brand=HP&brand=Dell")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'Ultra Compact': 0.005, 'All-in-One':0.05, 'Tower': 0.8, 'Mini-Tower': 0.6, 'Tiny': 0.4})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Desktop')
    list_par.append(list_par_tmp)
    run_pfv(list_par)

def Workstations():
    textbox.configure(state="normal")
    textbox.insert("end", "Starting Workstations data collection...\n\n")
    textbox.configure(state="disabled")
    button_notebooks.configure(state="disabled")
    button_desktops.configure(state="disabled")
    button_workstations.configure(state="disabled")
    button_mobile_workstations.configure(state="disabled")
    button_all.configure(state="disabled")
    button_cancel.configure(state="normal")    
    list_par = []
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/workstations/workstation?sortBy=stock%3Adesc&instock=true&brand=HP&brand=Lenovo&brand=Dell")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'Ultra Compact': 0.005, 'All-in-One':0.05, 'Tower': 0.8, 'Mini-Tower': 0.6, 'Tiny': 0.4})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Workstation')
    list_par.append(list_par_tmp)
    run_pfv(list_par)

def Mobile_Workstations():
    textbox.configure(state="normal")
    textbox.insert("end", "Starting Mobile Workstation data collection...\n")
    textbox.configure(state="disabled")
    button_notebooks.configure(state="disabled")
    button_desktops.configure(state="disabled")
    button_workstations.configure(state="disabled")
    button_mobile_workstations.configure(state="disabled")
    button_all.configure(state="disabled")
    button_cancel.configure(state="normal")
    list_par = []
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/notebooks/mobile-workstation?sortBy=stock%3Adesc&instock=true&brand=Lenovo&brand=HP&brand=Dell")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'12': 0.005, '13':0.05, '14': 0.3, '15': 0.6, '16': 0.7, '17': 0.9})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Mobile Workstation')
    list_par.append(list_par_tmp)
    run_pfv(list_par)

def All():
    textbox.configure(state="normal")
    textbox.insert("end", "Starting data collection for all this will take awhile...\n")
    textbox.configure(state="disabled")
    button_notebooks.configure(state="disabled")
    button_desktops.configure(state="disabled")
    button_workstations.configure(state="disabled")
    button_mobile_workstations.configure(state="disabled")
    button_all.configure(state="disabled")
    button_cancel.configure(state="normal")
    list_par = []
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/notebooks/notebook?instock=true&productType=Notebook&brand=HP&brand=Lenovo&brand=Dell")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'12': 0.005, '13':0.05, '14': 0.8, '15': 0.3, '16': 0.6, '17': 0.4})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Notebook')
    list_par.append(list_par_tmp)
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/desktop-computers?sortBy=stock%3Adesc&instock=true&brand=Lenovo&brand=HP&brand=Dell")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'Ultra Compact': 0.005, 'All-in-One':0.05, 'Tower': 0.8, 'Mini-Tower': 0.6, 'Tiny': 0.4})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Desktop')
    list_par.append(list_par_tmp)
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/workstations/workstation?sortBy=stock%3Adesc&instock=true&brand=HP&brand=Lenovo&brand=Dell")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'Ultra Compact': 0.005, 'All-in-One':0.05, 'Tower': 0.8, 'Mini-Tower': 0.6, 'Tiny': 0.4})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Workstation')
    list_par.append(list_par_tmp)
    list_par_tmp = []
    list_par_tmp.append("https://www.directdial.com/us/search/computer-systems/notebooks/mobile-workstation?sortBy=stock%3Adesc&instock=true&brand=Lenovo&brand=HP&brand=Dell")
    list_par_tmp.append("specs.csv")
    list_par_tmp.append('price.csv')
    list_par_tmp.append('stock.csv')
    list_par_tmp.append({'12': 0.005, '13':0.05, '14': 0.3, '15': 0.6, '16': 0.7, '17': 0.9})
    list_par_tmp.append('errors.csv')
    list_par_tmp.append('Mobile Workstation')
    list_par.append(list_par_tmp)
    run_pfv(list_par)

def Cancel():
    textbox.configure(state="normal")
    textbox.insert("end", "Data collection cancelled...\n")
    textbox.configure(state="disabled")
    stop_event.set()
    button_notebooks.configure(state="normal")
    button_desktops.configure(state="normal")
    button_workstations.configure(state="normal")
    button_mobile_workstations.configure(state="normal")
    button_cancel.configure(state="disabled")

def update_textbox(message):
    textbox.configure(state="normal")
    root.after(0, lambda: textbox.insert("end", message+"\n"))
    textbox.configure(state="disabled")

def check_queue():
    while not msg_queue.empty():
        msg = msg_queue.get()
        textbox.configure(state="normal")
        textbox.insert("end", msg)
        textbox.see("end")
        textbox.configure(state="disabled")
    root.after(100, check_queue)

def reset_buttons():
    button_notebooks.configure(state="normal")
    button_desktops.configure(state="normal")
    button_workstations.configure(state="normal")
    button_mobile_workstations.configure(state="normal")
    button_all.configure(state="normal")
    button_cancel.configure(state="disabled")

msg_queue = queue.Queue()
stop_event = threading.Event()

customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("blue")

root = customtkinter.CTk()
root.geometry("800x400")
root.title("Auto PFV Tool")

frame = customtkinter.CTkFrame(master=root)
frame.grid(row=1, column=0)

label = customtkinter.CTkLabel(master=frame, text="Auto PFV Tool", font=("Arial", 20))
label.grid(row=2, column=0, columnspan=5, pady=10)

button_notebooks = customtkinter.CTkButton(master=frame, text="Notebooks", command=Notebooks, state="normal")
button_notebooks.grid(row=4, column=0, padx=10, pady=10)
button_desktops = customtkinter.CTkButton(master=frame, text="Desktops", command=Desktops, state="normal")
button_desktops.grid(row=4, column=1, padx=10, pady=10)
button_workstations = customtkinter.CTkButton(master=frame, text="Workstations", command=Workstations, state="normal")
button_workstations.grid(row=4, column=2, padx=10, pady=10)
button_mobile_workstations = customtkinter.CTkButton(master=frame, text="Mobile Workstations", command=Mobile_Workstations, state="normal")
button_mobile_workstations.grid(row=4, column=3, padx=10, pady=10)
button_all = customtkinter.CTkButton(master=frame, text="All", command=All, state="normal")
button_all.grid(row=4, column=4, padx=10, pady=10)

textbox = customtkinter.CTkTextbox(master=frame, width=600)
textbox.grid(row=5, column=0, columnspan=5,padx=10, pady=10)
textbox.insert("end", "Select a category to start data collection...\n\n")
textbox.configure(state="disabled")

progressbar = customtkinter.CTkProgressBar(master=frame, orientation="horizontal")
progressbar.grid(row=6, column=0, columnspan=5, padx=10, pady=10)

button_cancel = customtkinter.CTkButton(master=frame, text="Cancel", command=Cancel, state="disabled")
button_cancel.grid(row=7, column=0, columnspan=5, padx=10, pady=10)

root.after(100, check_queue)
root.mainloop()








