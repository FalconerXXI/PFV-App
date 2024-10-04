import logging
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from base import Base
from history import DirectDialUSHistory, DirectDialCAHistory, HistoryManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the base class for shared fields
class DirectDialBase(Base):
    __abstract__ = True
    sku = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    category = Column(String)
    form_factor = Column(String)
    categories = Column(String)
    brand = Column(String)
    price = Column(Float)
    msrp = Column(Float)
    stock = Column(Integer)
    cpu = Column(String)
    gpu = Column(String)
    gpu_mem = Column(String)
    ddr = Column(String)
    warranty = Column(String)
    os = Column(String)
    ram = Column(String)
    screen_size = Column(String)
    screen_resolution = Column(String)
    touchscreen = Column(String)
    language = Column(String)
    storage = Column(String)
    wifi = Column(Boolean)
    wwan = Column(Boolean)
    url = Column(String)
    ff_score = Column(Float)
    cpu_score = Column(Float)
    gpu_score = Column(Float)
    storage_score = Column(Float)
    ram_score = Column(Float)
    total_score = Column(Float)
    date_added = Column(DateTime, default=func.now())
    date_updated = Column(DateTime, onupdate=func.now())
    in_stock = Column(Boolean, default=True)
    errors = Column(String)


# Define individual models inheriting from the base class
class DirectDialUS(DirectDialBase):
    __tablename__ = 'DirectDialUS'
    history = relationship("DirectDialUSHistory", back_populates="product")

class DirectDialCA(DirectDialBase):
    __tablename__ = 'DirectDialCA'
    history = relationship("DirectDialCAHistory", back_populates="product")


class ProductManager:
    def __init__(self, session):
        self.session = session
        self.history_manager = HistoryManager(session)

    def insert_or_update_product(self, product_data, table_class):
        try:
            # Helper function to flatten fields if they are lists
            def flatten_field(field):
                return ", ".join(field) if isinstance(field, list) else field

            # Retrieve SKU and handle missing SKU scenarios
            sku = product_data.get("id")
            if not sku:
                logger.warning("Skipping product without SKU.")
                return

            # Check for existing product in the database
            existing_product = self.session.query(table_class).filter_by(sku=sku).first()

            # Create a dictionary of new data based on available fields in the JSON
            new_data = {
                'sku': sku,
                'name': flatten_field(product_data.get("_Product_Family")),
                'category': flatten_field(product_data.get("productType")),
                'stock': int(product_data.get("stock", 0)) if product_data.get("stock") else None,
                'form_factor': flatten_field(product_data.get("_Form_Factor")),
                'categories': flatten_field(product_data.get("categories")[1]) if product_data.get("categories") and len(product_data.get("categories")) > 1 else None,
                'brand': flatten_field(product_data.get("brand")),
                'price': float(product_data.get("price", 0)) if product_data.get("price") else None,
                'msrp': float(product_data.get("msrp", 0)) if product_data.get("msrp") else None,
                'cpu': f'{flatten_field(product_data.get("_Processor_Manufacturer"))} {flatten_field(product_data.get("_Processor_Type"))} {flatten_field(product_data.get("_Processor_Model"))}',
                'gpu': f'{flatten_field(product_data.get("_Graphics_Controller_Manufacturer"))} {flatten_field(product_data.get("_Graphics_Controller_Model"))}',
                'gpu_mem': flatten_field(product_data.get("_Graphics_Memory_Accessibility")),
                'ddr': flatten_field(product_data.get("_Graphics_Memory_Technology")),
                'warranty': flatten_field(product_data.get("_Limited_Warranty_Duration")),
                'os': flatten_field(product_data.get("_Operating_System")),
                'ram': flatten_field(product_data.get("_Standard_Memory")) if product_data.get("_Standard_Memory") else flatten_field(product_data.get("_Total_Installed_System_Memory")),
                'screen_size': flatten_field(product_data.get("_Screen_Size")),
                'screen_resolution': flatten_field(product_data.get("_Screen_Resolution")),
                'touchscreen': flatten_field(product_data.get("_Touchscreen")),
                'language': flatten_field(product_data.get("_Keyboard_Localization")),
                'storage': flatten_field(product_data.get("_Total_Solid_State_Drive_Capacity")) if product_data.get("_Total_Solid_State_Drive_Capacity") else flatten_field(product_data.get("_Flash_Memory_Capacity")),
                'wifi': True if product_data.get("_Wireless_LAN_Standard") else False,
                'wwan': True if product_data.get("_WWAN_Supported") else False,
                'url': f'http://www.directdial.com/{table_class.__tablename__[-2:]}/{flatten_field(product_data.get("url"))}'
            }

            # Update existing product or insert a new one
            if existing_product:
                for key, value in new_data.items():
                    if key in ['price', 'stock'] or getattr(existing_product, key) in [None, '']:
                        setattr(existing_product, key, value)
                logger.info(f"Updated product with SKU: {sku}")
            else:
                new_product = table_class(**new_data)
                self.session.add(new_product)
                logger.info(f"Inserted new product with SKU: {sku}")

            # Log history and commit transaction
            self.history_manager.log_price_stock_history(existing_product if existing_product else new_product, table_class)
            self.session.commit()
        except Exception as e:
            logger.exception(f"Error inserting or updating product with SKU: {sku}")
            self.session.rollback()

    def load_products_from_json(self, file_path, table_class):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                for item in data:
                    product_data = item.get('document') 
                    if product_data:
                        self.insert_or_update_product(product_data, table_class)
                    else:
                        logger.warning("No 'document' key found in JSON item.")
            logger.info(f"Loaded products from {file_path} into {table_class.__tablename__}")
        except Exception as e:
            logger.exception(f"Error loading products from {file_path}")
            self.session.rollback()
