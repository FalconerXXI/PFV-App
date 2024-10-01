import logging
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from base import Base  # Import Base from base.py

# Configure logging
logger = logging.getLogger(__name__)

class DirectDialHistoryBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DirectDialUSHistory(DirectDialHistoryBase):
    __tablename__ = 'DirectDialUSHistory'
    sku = Column(String, ForeignKey('DirectDialUS.sku'), nullable=False)
    product = relationship("DirectDialUS", back_populates="history")

class DirectDialCAHistory(DirectDialHistoryBase):
    __tablename__ = 'DirectDialCAHistory'
    sku = Column(String, ForeignKey('DirectDialCA.sku'), nullable=False)
    product = relationship("DirectDialCA", back_populates="history")

class HistoryManager:
    def __init__(self, session):
        self.session = session

    def log_price_stock_history(self, product, table_class):
        """Log the price and stock for each product to the respective history table."""
        try:
            if table_class.__tablename__ == 'DirectDialUS':
                history_record = DirectDialUSHistory(
                    sku=product.sku,
                    price=product.price or 0.0,
                    stock=product.stock or 0
                )
            elif table_class.__tablename__ == 'DirectDialCA':
                history_record = DirectDialCAHistory(
                    sku=product.sku,
                    price=product.price or 0.0,
                    stock=product.stock or 0
                )
            else:
                logger.error("Unknown table class for history logging.")
                return

            # Add the history record to the session
            self.session.add(history_record)
            logger.info(f"Logged history for product SKU: {product.sku}")
        except Exception as e:
            logger.exception(f"Error logging history for product SKU: {product.sku}")
            self.session.rollback()
