import logging
import json
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, relationship
from base import Base
from history import DirectDialUSHistory, DirectDialCAHistory, HistoryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sqlalchemy import Float

from sqlalchemy import Float, Integer, String, Column

from sqlalchemy import Float, Integer, String, Column, DateTime, Boolean
from sqlalchemy.sql import func

class DirectDialBase(Base):
    __abstract__ = True
    sku = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    category = Column(String)
    formFactor = Column(String)
    categories = Column(String)
    brand = Column(String)
    price = Column(Float)
    msrp = Column(Float)
    stock = Column(Integer)
    processorManufacturer = Column(String)
    chipset = Column(String)
    processorType = Column(String)
    processorModel = Column(String)
    graphicsControllerManufacturer = Column(String)
    graphicsControllerModel = Column(String)
    graphicsMemoryAccessibility = Column(String)
    graphicsMemoryTechnology = Column(String)
    limitedWarrantyDuration = Column(String)
    operatingSystem = Column(String)
    standardMemory = Column(String)
    totalInstalledSystemMemory = Column(String)
    screenSize = Column(String)
    screenResolution = Column(String)
    screenMode = Column(String)
    touchscreen = Column(String)
    keyboardLocalization = Column(String)
    totalSolidStateDriveCapacity = Column(String)
    flashMemoryCapacity = Column(String)
    wirelessLanStandard = Column(String)
    wwanSupported = Column(String)
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
            def flatten_field(field):
                if isinstance(field, list):
                    return ", ".join(field)
                return field
            sku = product_data.get("id")
            if not sku:
                logger.warning("Skipping product without SKU.")
                return

            existing_product = self.session.query(table_class).filter_by(sku=sku).first()

            new_data = {
                'sku': sku,
                'name': flatten_field(product_data.get("_Product_Family")),
                'category': flatten_field(product_data.get("productType")),
                'stock': int(product_data.get("stock", 0)) if product_data.get("stock") else None,
                'formFactor': flatten_field(product_data.get("_Form_Factor")),
                'categories': flatten_field(product_data.get("categories")[1]) if product_data.get("categories") and len(product_data.get("categories")) > 1 else None,
                'brand': flatten_field(product_data.get("brand")),
                'price': float(product_data.get("price", 0)) if product_data.get("price") else None,
                'msrp': float(product_data.get("msrp", 0)) if product_data.get("msrp") else None,
                'processorManufacturer': flatten_field(product_data.get("_Processor_Manufacturer")),
                'chipset': flatten_field(product_data.get("_Chipset")),
                'processorType': flatten_field(product_data.get("_Processor_Type")),
                'processorModel': flatten_field(product_data.get("_Processor_Model")),
                'graphicsControllerManufacturer': flatten_field(product_data.get("_Graphics_Controller_Manufacturer")),
                'graphicsControllerModel': flatten_field(product_data.get("_Graphics_Controller_Model")),
                'graphicsMemoryAccessibility': flatten_field(product_data.get("_Graphics_Memory_Accessibility")),
                'graphicsMemoryTechnology': flatten_field(product_data.get("_Graphics_Memory_Technology")),
                'limitedWarrantyDuration': flatten_field(product_data.get("_Limited_Warranty_Duration")),
                'operatingSystem': flatten_field(product_data.get("_Operating_System")),
                'standardMemory': flatten_field(product_data.get("_Standard_Memory")),
                'totalInstalledSystemMemory': flatten_field(product_data.get("_Total_Installed_System_Memory")),
                'screenSize': flatten_field(product_data.get("_Screen_Size")),
                'screenResolution': flatten_field(product_data.get("_Screen_Resolution")),
                'screenMode': flatten_field(product_data.get("_Screen_Mode")),
                'touchscreen': flatten_field(product_data.get("_Touchscreen")),
                'keyboardLocalization': flatten_field(product_data.get("_Keyboard_Localization")),
                'totalSolidStateDriveCapacity': flatten_field(product_data.get("_Total_Solid_State_Drive_Capacity")),
                'flashMemoryCapacity': flatten_field(product_data.get("_Flash_Memory_Capacity")),
                'wirelessLanStandard': flatten_field(product_data.get("_Wireless_LAN_Standard")),
                'wwanSupported': flatten_field(product_data.get("_WWAN_Supported")),
                'url': flatten_field(product_data.get("url"))
            }

            if existing_product:
                for key, value in new_data.items():
                    if getattr(existing_product, key) in [None, ''] or key in ['price', 'stock']:
                        setattr(existing_product, key, value)
                logger.info(f"Updated product with SKU: {sku}")
            else:
                existing_product = table_class(**new_data)
                self.session.add(existing_product)
                logger.info(f"Inserted new product with SKU: {sku}")
            self.history_manager.log_price_stock_history(existing_product, table_class)
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
