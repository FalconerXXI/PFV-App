from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
        """General method to add or update CPU or GPU."""
        session = self.get_session()
        try:
            # Query the specific hardware table (CPU or GPU)
            hardware = session.query(hardware_class).filter_by(name=name).first()
            if hardware:
                hardware.score = score
            else:
                # Create a new instance for CPU or GPU
                hardware = hardware_class(name=name, score=score)
                session.add(hardware)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error adding/updating hardware: {e}")
        finally:
            session.close()

    def get_all_hardware_scores(self, hardware_type):
        """Extracts all hardware names and their scores for the given type (CPU or GPU)."""
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