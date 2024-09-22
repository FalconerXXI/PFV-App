from hardware import CPU, GPU, Hardware
from products import ProductManager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from products import ProductManager, Product
from sqlalchemy.exc import SQLAlchemyError
import logging
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import re

class Score:
    def __init__(self, product_db, hardware_db):
        self.hardware_db = hardware_db
        self.product_db = product_db
        try:
            self.engine_cdw = create_engine(self.product_db)
            self.Session_cdw = sessionmaker(bind=self.engine_cdw)
            self.engine_hardware = create_engine(self.hardware_db)
            self.Session_hardware = sessionmaker(bind=self.engine_hardware)
        except SQLAlchemyError as e:
            logging.error(f"Error initializing database connections: {e}")
            raise


    def calculate_scores(self):
        try:
            session_cdw = self.Session_cdw()
            session_hardware = self.Session_hardware()
            products = session_cdw.query(Product).filter_by(scanned=True).yield_per(100)
            cpus = {cpu.name: cpu for cpu in session_hardware.query(CPU).all()}
            gpus = {gpu.name: gpu for gpu in session_hardware.query(GPU).all()}
            cpu_names = list(cpus.keys())
            gpu_names = list(gpus.keys())
            try:
                for product in products:
                    if product.cpu in cpus:
                        matched_cpu_name = product.cpu  # Exact match found
                    else:
                        matched_cpu_name = self.fuzzy_match_name(product.cpu, cpu_names)  # Fuzzy match if no exact match

                    # Check for an exact GPU match first
                    if product.gpu in gpus:
                        matched_gpu_name = product.gpu  # Exact match found
                    else:
                        matched_gpu_name = self.fuzzy_match_name(product.gpu, gpu_names)  # Fuzzy match if no exact match

                    # Only score if a match is found
                    if matched_cpu_name:
                        product.cpu_score = self.hardware_score(matched_cpu_name, cpus)
                    else:
                        logging.warning(f"No suitable match found for CPU: {product.cpu}")

                    if matched_gpu_name:
                        product.gpu_score = self.hardware_score(matched_gpu_name, gpus)
                    else:
                        logging.warning(f"No suitable match found for GPU: {product.gpu}")
            
                    product.storage_score = self.storage_score(product.storage)
                    product.ram_score = self.ram_score(product.ram)
                    product.ff_score = self.ff_score(product.form_factor)
                    session_cdw.commit()
                    print(f"Product {product.sku}, CPU Score: {product.cpu_score}, GPU Score: {product.gpu_score}, Storage Score: {product.storage_score}, RAM Score: {product.ram_score}")
           
            except KeyError as e:
                logging.warning(f"Hardware not found for product {product.sku}: {e}")
                session_cdw.rollback()  # Rollback only if there's an issue with this product
            except Exception as e:
                logging.error(f"Error processing product {product.sku}: {e}")
                session_cdw.rollback()  # Rollback for this product only and move to the next product

        except SQLAlchemyError as e:
            logging.error(f"Database query failed: {e}")
            if session_cdw:
                session_cdw.rollback()  # Rollback session-wide only for SQLAlchemy-related errors

        finally:
            if session_cdw:
                session_cdw.close()
            if session_hardware:
                session_hardware.close()

    @classmethod
    def hardware_score(cls, hardware_name, hardwares):
        try:
            if hardware_name == "N/A":
                return 0
            if hardware_name == "Integrated":
                return 1
            if hardware_name in hardwares:
                return hardwares[hardware_name].score
            else:
                logging.warning(f"No match found for hardware: {hardware_name}")
                return 0
        except KeyError as e:
            logging.error(f"KeyError in hardware_score: {e}")
            return 0
        except Exception as e:
            logging.error(f"Unexpected error in hardware_score: {e}")
            return 0

    @classmethod
    def storage_score(cls, storage):
        try:
            if storage == "N/A" or storage is None:
                return 0
            return storage
        except TypeError as e:
            logging.error(f"TypeError calculating storage score: {e}")
            return 0
        except Exception as e:
            logging.error(f"Unexpected error calculating storage score: {e}")
            return 0

    @classmethod
    def ram_score(cls, ram):
        try:
            if ram == "N/A" or ram is None:
                return 0
            return ram 
        except TypeError as e:
            logging.error(f"TypeError calculating RAM score: {e}")
            return 0
        except Exception as e:
            logging.error(f"Unexpected error calculating RAM score: {e}")
            return 0

    @classmethod
    def ff_score(cls, ff_value):
        try:
            if ff_value.isdigit():
                screen_size = int(ff_value)
                return screen_size*.01
            elif isinstance(ff_value, str):
                ff_value = ff_value.lower()
                if ff_value == 'tiny':
                    return 2
                elif ff_value == 'sff':
                    return 3
                elif ff_value == 'tower':
                    return 4
                elif ff_value == 'all-in-one':
                    return 1
                else:
                    logging.error(f"Invalid desktop model: {ff_value}")
                    return 0
            else:
                logging.error(f"Invalid form factor value: {ff_value}")
                return 0

        except Exception as e:
            logging.error(f"Unexpected error in ff_score: {e}")
            return 0

    @classmethod 
    def fuzzy_match_name(cls, product_name, hardware_names, threshold=80):
        original_hardware_names = hardware_names
        cleaned_product_name = cls.remove_brand(product_name)
        cleaned_hardware_names = [cls.remove_brand(name) for name in hardware_names]
        best_match_cleaned, score = process.extractOne(cleaned_product_name, cleaned_hardware_names)
        if best_match_cleaned:
            best_match_original = original_hardware_names[cleaned_hardware_names.index(best_match_cleaned)]
        logging.info(f"Attempting to match '{cleaned_product_name}' (original: '{product_name}') "
                    f"- Best match: '{best_match_original}' with score: {score}%")
        if score >= threshold:
            logging.info(f"Fuzzy matched '{product_name}' to '{best_match_original}' with score {score}%")
            return best_match_original
        else:
            logging.info(f"No suitable match for '{product_name}' (best score was {score}%)")
            return None
        
    @classmethod
    def remove_brand(cls, name):
        # Define patterns for common CPU and GPU brands to remove
        brand_patterns = [
            r'\bIntel\b',
            r'\bAMD\b',
            r'\bNVIDIA\b',
            r'\bGeForce\b',
            r'\bRadeon\b',
            r'\bEmbedded\b',
            r'\bRyzen\b',
        ]
        
        # Remove each brand pattern
        for pattern in brand_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Strip extra spaces after removing brand names
        return name.strip()