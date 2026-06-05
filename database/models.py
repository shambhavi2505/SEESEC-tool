from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

Base=declarative_base()

class ContentItem(Base):
    __tablename__="content_items"
    id=Column(Integer, primary_key=True, autoincrement=True)
    competitor_name=Column(String(100), nullable=False)
    content_type=Column(String(50))
    title=Column(Text, nullable=False)
    url=Column(Text, nullable=False, unique=True)
    published_date=Column(String(50))
    topics=Column(Text)
    keywords=Column(Text)
    summary=Column(Text)
    scraped_time=Column(DateTime, default=datetime.utcnow)

class Opportunity(Base):
    __tablename__="opportunities"
    id=Column(Integer, primary_key=True, autoincrement=True)
    topics=Column(String(100))
    competitor_count=Column(Integer)
    competitor_name_covering=Column(Text)
    suggested_title=Column(Text)
    reason=Column(Text)
    created_time=Column(DateTime, default=datetime.utcnow)

DATABASE_url="sqlite:///./competitor_data.db"
engine=create_engine(DATABASE_url)
SessionLocal=sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database intialised successfully!")


if __name__=="__main__":
    init_db()
    






