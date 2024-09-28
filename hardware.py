from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from selenium_stealth import stealth

Base = declarative_base()

class Hardware(Base):
    __abstract__ = True  # Prevent this base class from creating a table
    name = Column("name", String, primary_key=True)
    score = Column("score", Float)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, {self.score})"

class CPU(Hardware):
    __tablename__ = 'cpus'

class GPU(Hardware):
    __tablename__ = 'gpus'

class HardwareManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def add_hardware(self, name, score, hardware_class):
        session = self.get_session()
        try:
            hardware = session.query(hardware_class).filter_by(name=name).first()
            if hardware:
                hardware.score = score
            else:
                hardware = hardware_class(name=name, score=score)
                session.add(hardware)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error adding/updating hardware: {e}")
        finally:
            session.close()

    def get_all_hardware_scores(self, hardware_type):
        session = self.get_session()
        try:
            hardware_list = session.query(hardware_type).all()
            scores = {hardware.name: hardware.score for hardware in hardware_list}
            return scores
        except Exception as e:
            print(f"Error retrieving {hardware_type} scores: {e}")
            return {}
        finally:
            session.close()

class HardwareScraper:
    def __init__(self, url):
        self.url = url

    def scrape_hardware(self):
        print(f"Scraping Hardware Scores from: {self.url}")
        options = uc.ChromeOptions() 
        options.headless = True
        driver = uc.Chrome(use_subprocess=True, options=options)
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True) 
        driver.get(self.url)
        wait = WebDriverWait(driver, 20)
        item_table = wait.until(EC.visibility_of_element_located((By.ID, 'cputable')))
        item_html = item_table.get_attribute("innerHTML")
        driver.close()
        soup = BeautifulSoup(item_html, 'lxml')
        hardware = soup.find('tbody').find_all('tr')
        for item in hardware:
            name = item.find('a').text.split('@')[0].strip() if item.find('a') else None
            score = int(item.find_all('td')[1].text.replace(',', '')) if len(item.find_all('td')) > 1 else None
            if name and score:
                hardware_manager = HardwareManager('sqlite:///hardware.db')
                if 'cpu' in self.url:
                    hardware_manager.add_hardware(name, score, CPU)
                elif 'gpu' in self.url:
                    hardware_manager.add_hardware(name, score, GPU)
        print("Scraping Complete")