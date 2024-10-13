import requests
import time
import json
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
from contextlib import contextmanager

Base = declarative_base()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Hardware(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tdp = Column(String, nullable=True)
    date = Column(String, nullable=True)
    cat = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    samples = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class CPU(Hardware):
    __tablename__ = 'cpu'
    cpumark = Column(String, nullable=True)
    thread = Column(String, nullable=True)
    socket = Column(String, nullable=True)
    speed = Column(String, nullable=True)
    turbo = Column(String, nullable=True)
    cores = Column(String, nullable=True)
    secondaryCores = Column(String, nullable=True)
    secondaryLogicals = Column(String, nullable=True)

class GPU(Hardware):
    __tablename__ = 'gpu'
    g3d = Column(String, nullable=True)
    g2d = Column(String, nullable=True)
    bus = Column(String, nullable=True)
    memSize = Column(String, nullable=True)
    coreClk = Column(String, nullable=True)
    memClk = Column(String, nullable=True)

class HardwareBenchmarkScraper:
    def __init__(self, config_path, db_url="sqlite:///products.db"):
        self.config = self.load_config(config_path)
        if not self.config.get('cpu') or not self.config.get('gpu'):
            raise ValueError("Configuration file is missing 'cpu' or 'gpu' sections.")
        
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    @staticmethod
    def load_config(config_path):
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading config: {e}")
            raise

    @staticmethod
    def generate_timestamp():
        return str(int(time.time() * 1000))

    @contextmanager
    def db_session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            session.close()

    def initialize_session(self, init_url, headers):
        try:
            response = self.session.get(init_url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to initialize session: {e}")
            raise

    def send_request_and_save_to_db(self, data_url, headers, benchmark_type):
        timestamp = self.generate_timestamp()
        querystring = {"_": timestamp}
        
        try:
            response = self.session.get(data_url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            if "data" not in data or not isinstance(data["data"], list):
                logger.warning("Invalid data format received.")
                return
            
            def safe_int(value, default=None):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            with self.db_session_scope() as db_session:
                for item in data.get("data", []):
                    hardware = self.create_hardware_instance(benchmark_type, item, safe_int)
                    if hardware:
                        db_session.merge(hardware)
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def create_hardware_instance(self, benchmark_type, item, safe_int):
        common_fields = {
            'id': safe_int(item.get("id")),
            'name': item.get("name"),
            'tdp': item.get("tdp"),
            'date': item.get("date"),
            'cat': item.get("cat"),
            'rank': safe_int(item.get("rank")),
            'samples': item.get("samples")
        }
        
        if benchmark_type == 'cpu':
            return CPU(
                **common_fields,
                cpumark=item.get("cpumark"),
                thread=item.get("thread"),
                socket=item.get("socket"),
                speed=item.get("speed"),
                turbo=item.get("turbo"),
                cores=item.get("cores"),
                secondaryCores=item.get("secondaryCores"),
                secondaryLogicals=item.get("secondaryLogicals")
            )
        elif benchmark_type == 'gpu':
            return GPU(
                **common_fields,
                g3d=item.get("g3d"),
                g2d=item.get("g2d"),
                bus=item.get("bus"),
                memSize=item.get("memSize"),
                coreClk=item.get("coreClk"),
                memClk=item.get("memClk")
            )
        return None

    def run(self):
        with requests.Session() as session:
            self.session = session
            for section, config in self.config.items():
                init_url = config.get("init_url")
                data_url = config.get("data_url")
                headers = config.get("headers", {})
                if not init_url or not data_url or not headers:
                    logger.warning(f"Skipping section {section}: missing URLs or headers.")
                    continue
                
                self.initialize_session(init_url, headers)
                self.send_request_and_save_to_db(data_url, headers, section)

if __name__ == "__main__":
    scraper = HardwareBenchmarkScraper("hardware_website_info.json")
    scraper.run()
