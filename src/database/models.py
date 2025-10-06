"""Database models for storing jobs and scores"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Job(Base):
    """Job posting model"""
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)

    # Job identifiers
    job_url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)

    # Job details
    location = Column(String)
    job_type = Column(String)  # fulltime, contract, etc.
    is_remote = Column(Boolean, default=False)
    description = Column(Text)

    # Compensation
    min_salary = Column(Float)
    max_salary = Column(Float)
    salary_currency = Column(String, default="USD")

    # Metadata
    source = Column(String)  # linkedin, indeed, etc.
    posted_date = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # AI Scoring (JSON field for structured scores)
    ai_score = Column(JSON)  # Stores the complete scoring output
    overall_score = Column(Float, index=True)  # Denormalized for quick sorting

    # Status tracking
    is_scored = Column(Boolean, default=False, index=True)
    is_applied = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    notes = Column(Text)

    def __repr__(self):
        return f"<Job(title='{self.title}', company='{self.company}', score={self.overall_score})>"


class ScanHistory(Base):
    """Track job scan history"""
    __tablename__ = 'scan_history'

    id = Column(Integer, primary_key=True)
    scan_date = Column(DateTime, default=datetime.utcnow, index=True)
    jobs_found = Column(Integer)
    jobs_scored = Column(Integer)
    search_criteria = Column(JSON)  # Store the search params used

    def __repr__(self):
        return f"<ScanHistory(date='{self.scan_date}', jobs={self.jobs_found})>"


def create_tables(database_url: str = "sqlite:///vacai.db"):
    """Create all database tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(database_url: str = "sqlite:///vacai.db"):
    """Get database session"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()
