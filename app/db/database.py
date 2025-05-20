# app/db/database.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.orm').setLevel(logging.ERROR)
# 본인의 DB 정보로 수정하세요
DATABASE_URL = "mysql+pymysql://root:0000@localhost:3306/mydb"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# 테이블 생성용
def create_tables():
    Base.metadata.create_all(bind=engine)
