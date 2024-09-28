from sqlalchemy import create_engine, Column, String, Float, Integer, PrimaryKeyConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
import csv

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    sku = Column("SKU", String, primary_key=True)
    type = Column("type", String, default="N/A")
    name = Column("name", String, default="N/A")
    brand = Column("brand", String, default="N/A")   
    form_factor = Column("form factor", String, default="N/A")
    stock = Column("stock", Integer, default=0)
    price = Column("price", Float, default=0.0)
    msrp = Column("msrp", Float, default=0.0)
    rebate = Column("rebate", Float, default=0.0)
    sale = Column("sale", Float, default=0.0)
    cpu = Column("CPU", String, default="N/A")
    gpu = Column("GPU", String, default="N/A")
    storage = Column("storage", Integer, default=0)
    ram = Column("RAM", Integer, default=0)
    ddr = Column("DDR", String, default="N/A")
    os = Column("OS", String, default="N/A")
    keyboard = Column("keyboard", String, default="N/A")
    ethernet = Column("ethernet", String, default="N/A")
    wifi = Column("WiFi", String, default="N/A")
    warranty = Column("warranty", Integer, default=0)
    screen_res = Column("screen res.", String, default="N/A")
    screen_type = Column("screen type", String, default="N/A")
    screen_size = Column("screen size", String, default="N/A")
    touch = Column("touch", String, default="N/A") 
    cpu_score = Column("cpu score", Integer, default=0)
    gpu_score = Column("gpu score", Integer, default=0)
    ff_score = Column("ff score", Integer, default=0)
    ram_score = Column("ram score", Integer, default=0)
    storage_score = Column("storage score", Integer, default=0)
    score = Column("score", Integer, default=0)
    url = Column("url", String, default="N/A")
    orig_cpu = Column("orig. cpu", String, default="N/A")
    orig_gpu = Column("orig. gpu", String, default="N/A")
    updated = Column("updated", String, default="N/A")
    discovered = Column("discovered", String, default="N/A")
    error = Column("error", Boolean, default=False)
    scanned = Column("scanned", Boolean, default=False)

    def __repr__(self):
        return f"Product({self.sku}, {self.price}, {self.url}, {self.updated})"

class ProductManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def add_cdw_product(self, sku, price, type, url, updated, discovered):
        session = self.get_session()
        try:
            product = session.query(Product).filter_by(sku=sku).first()
            if product:
                product.price = price
                product.type = type
                product.url = url
                product.updated = updated
                product.discovered = discovered
            else:
                product = Product(sku=sku, price=price, type=type, url=url, updated=updated, discovered=discovered)
                session.add(product)   
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error adding/updating product: {e}")
        finally:
            session.close()

    def add_direct_dial_product(self, sku, stock, price, msrp, rebate, sale, brand, type, url, updated, discovered):
        session = self.get_session()
        try:
            product = session.query(Product).filter_by(sku=sku).first()
            if product:
                product.price = price
                product.stock = stock
                product.msrp = msrp
                product.rebate = rebate
                product.sale = sale
                product.brand = brand
                product.type = type
                product.url = url
                product.updated = updated
                product.discovered = discovered
            else:
                product = Product(sku=sku, price=price, stock=stock, msrp=msrp, rebate=rebate, sale=sale, brand=brand,type=type, url=url, updated=updated, discovered=discovered)
                session.add(product)  
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error adding/updating product: {e}")
        finally:
            session.close()

    def get_products(self):
        session = self.get_session()
        products = session.query(Product).all()
        session.close()
        return products
    
#class Price(Base):
#    __tablename__ = 'prices'
#    sku = Column("sku", String)
#    date = Column("date", String)
#    price = Column("price", Float)
#    __table_args__ = (PrimaryKeyConstraint('sku', 'date'),)

#    def __repr__(self):
#        return f"PriceTracker(SKU: {self.sku}, Date: {self.date}, Price: {self.price})"
    
#class Stock(Base):
#
#    __tablename__ = 'stocks'
#    sku = Column("sku", String)
#    date = Column("date", String)
#    stock = Column("stock", Float)
#    __table_args__ = (PrimaryKeyConstraint('sku', 'date'),)#

#    def __repr__(self):
#        return f"PriceTracker(SKU: {self.sku}, Date: {self.date}, Stock: {self.stock})"

class DatabaseExporter:
    def __init__(self, db_path):

        self.db_path = db_path
    def export_table_to_csv(self, table_name, csv_file_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(column_names)
                writer.writerows(rows)
            print(f"Data from table '{table_name}' has been exported to '{csv_file_path}'.")
        except Exception as e:
            print(f"Error exporting table '{table_name}': {e}")
        finally:
            conn.close()

