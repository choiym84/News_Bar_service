# app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base

# 본인의 DB 정보로 수정하세요
DATABASE_URL = "mysql+pymysql://root:0000@localhost:3306/mydb"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테이블 생성용
def create_tables():
    Base.metadata.create_all(bind=engine)
