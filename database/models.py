import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
)
from datetime import datetime


Base = declarative_base()


# ============================================================
# COMPANY
# ============================================================

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
        unique=True,
        index=True
    )

    website = Column(
        Text,
        nullable=False
    )

    # --------------------------------------------------------
    # Company intelligence
    # --------------------------------------------------------

    description = Column(
        Text,
        nullable=True
    )

    industry = Column(
        String(100),
        nullable=True
    )
    social_links = Column(
        Text,
        nullable=True
    )
    tech_stack = Column(
        Text,
        nullable=True
    )
    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    ai_summary = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Scraping / caching
    # --------------------------------------------------------

    scrape_status = Column(
        String(30),
        default="never_scraped"
    )

    pages_discovered = Column(
        Integer,
        default=0
    )

    pages_scanned = Column(
        Integer,
        default=0
    )

    articles_found = Column(
        Integer,
        default=0
    )

    last_scraped = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    social_profiles = relationship(
        "SocialProfile",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    scrape_runs = relationship(
        "ScrapeRun",
        back_populates="company",
        cascade="all, delete-orphan"
    )


# ============================================================
# EXISTING CONTENT TABLE
# ============================================================

class ContentItem(Base):

    __tablename__ = "content_items"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    competitor_name = Column(
        String(100),
        nullable=False,
        index=True
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


# ============================================================
# EXISTING OPPORTUNITIES TABLE
# ============================================================

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


# ============================================================
# SOCIAL PROFILES
# ============================================================

class SocialProfile(Base):

    __tablename__ = "social_profiles"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
        index=True
    )

    platform = Column(
        String(50),
        nullable=False
    )

    profile_url = Column(
        Text,
        nullable=False
    )

    discovered_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    company = relationship(
        "Company",
        back_populates="social_profiles"
    )

    __table_args__ = (
        Index(
            "idx_social_company_platform",
            "company_id",
            "platform"
        ),
    )


# ============================================================
# SCRAPE RUN HISTORY
# ============================================================

class ScrapeRun(Base):

    __tablename__ = "scrape_runs"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
        index=True
    )

    started_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )

    status = Column(
        String(30),
        default="running"
    )

    pages_discovered = Column(
        Integer,
        default=0
    )

    pages_scanned = Column(
        Integer,
        default=0
    )

    articles_found = Column(
        Integer,
        default=0
    )

    error_message = Column(
        Text,
        nullable=True
    )

    company = relationship(
        "Company",
        back_populates="scrape_runs"
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================
#
# Locally (no DATABASE_URL env var set) this falls back to the
# same SQLite file as before, so local dev is unaffected.
#
# On Render, DATABASE_URL will be set to the Postgres "Internal
# Database URL" you copy from the Postgres dashboard page.
#
# Render's Postgres URLs are given in the "postgres://" form,
# but SQLAlchemy 1.4+ / psycopg2 require "postgresql://" — so
# we rewrite the prefix if needed.
# ============================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./competitor_data.db",
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

# SQLite needs this special connect_arg (single-thread check);
# Postgres does not use or accept it.
connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


# ============================================================
# DATABASE MIGRATION
# ============================================================

def migrate_existing_database():

    """
    Adds new Phase 2 columns to the existing companies table.

    SQLAlchemy create_all() does not modify existing tables,
    therefore these ALTER TABLE statements are required.
    """

    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    if "companies" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("companies")
    }

    new_columns = {
        "description": "TEXT",
        "industry": "VARCHAR(100)",
        "scrape_status": "VARCHAR(30)",
        "pages_discovered": "INTEGER",
        "pages_scanned": "INTEGER",
        "articles_found": "INTEGER",
        "last_scraped": "DATETIME",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    }

    with engine.begin() as connection:

        for column_name, column_type in new_columns.items():

            if column_name not in existing_columns:

                print(
                    f"[DB] Adding column: {column_name}"
                )

                connection.execute(
                    text(
                        f"ALTER TABLE companies "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    print("=" * 60)
    print("SEESEC DATABASE INITIALIZATION")
    print("=" * 60)

    # First create existing tables
    Base.metadata.create_all(
        bind=engine
    )

    # Then migrate existing tables
    migrate_existing_database()

    # Create any new Phase 2 tables
    Base.metadata.create_all(
        bind=engine
    )

    print()
    print("[OK] Database initialized successfully.")
    print("[OK] Phase 1 tables preserved.")
    print("[OK] Phase 2 tables ready.")
    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    init_db()