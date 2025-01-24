from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

class StoreManager:
    engine = create_engine('sqlite:///mydatabase.db')  # 例如使用 SQLite 数据库
    Base = declarative_base()
    
    @staticmethod
    def init_db():  
        StoreManager.Base.metadata.create_all(StoreManager.engine)

    def get_session():
        return sessionmaker(bind=StoreManager.engine)()