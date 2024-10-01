
from hardware import CPU, GPU, Hardware
from products import ProductManager, Product
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from fuzzywuzzy import process, fuzz
import re

class Score:
    def __init__(self, session_product, session_hardware):
        # Initialize using existing sessions to ensure compatibility
        self.session_product = session_product
        self.session_hardware = session_hardware

    def calculate_scores(self):
        try:
            # Query for products and hardware components
            products = self.session_product.query(Product).filter_by(scanned=True).yield_per(100)
            cpus = {cpu.name: cpu for cpu in self.session_hardware.query(CPU).all()}
            gpus = {gpu.name: gpu for gpu in self.session_hardware.query(GPU).all()}
            
            # Create lists of CPU and GPU names for fuzzy matching
            cpu_names = list(cpus.keys())
            gpu_names = list(gpus.keys())

            # Iterate through products and update scores based on matches
            for product in products:
                if product.cpu:
                    # Fuzzy match CPU
                    match_cpu = process.extractOne(product.cpu, cpu_names, scorer=fuzz.ratio)
                    if match_cpu and match_cpu[1] > 80:  # Set a match threshold
                        product.cpu_match = cpus[match_cpu[0]]
                
                if product.gpu:
                    # Fuzzy match GPU
                    match_gpu = process.extractOne(product.gpu, gpu_names, scorer=fuzz.ratio)
                    if match_gpu and match_gpu[1] > 80:
                        product.gpu_match = gpus[match_gpu[0]]

            # Commit changes after updating product matches
            self.session_product.commit()

        except SQLAlchemyError as e:
            logging.error(f"Error calculating scores: {e}")
            self.session_product.rollback()
