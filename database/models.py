from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime


Base = declarative_base()


# ==========================================
# NEW: COMPANY TABLE
# ==========================================

class Company(Base):

    __tablename__ = "companies"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(
        String(100),
        nullable=False,
        unique=True
    )

    website = Column(
        Text,
        nullable=False
    )

    ai_summary = Column(
        Text,
        nullable=True
    )

    last_scraped = Column(
        DateTime,
        default=datetime.utcnow
    )
# ==========================================
# EXISTING CONTENT TABLE
# ==========================================

class ContentItem(Base):

    __tablename__ = "content_items"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    competitor_name = Column(
        String(100),
        nullable=False
    )

    content_type = Column(
        String(50)
    )

    title = Column(
        Text,
        nullable=False
    )

    url = Column(
        Text,
        nullable=False,
        unique=True
    )

    published_date = Column(
        String(50)
    )

    topics = Column(
        Text
    )

    keywords = Column(
        Text
    )

    summary = Column(
        Text
    )

    scraped_time = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================
# EXISTING OPPORTUNITIES TABLE
# ==========================================

class Opportunity(Base):

    __tablename__ = "opportunities"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    topics = Column(
        String(100)
    )

    competitor_count = Column(
        Integer
    )

    competitor_name_covering = Column(
        Text
    )

    suggested_title = Column(
        Text
    )

    reason = Column(
        Text
    )

    created_time = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================
# DATABASE CONNECTION
# ==========================================

DATABASE_URL = "sqlite:///./competitor_data.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine
)


# ==========================================
# CREATE TABLES
# ==========================================

def init_db():

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Database initialized successfully!"
    )


if __name__ == "__main__":

    init_db()