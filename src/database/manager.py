"""Database manager for CRUD operations"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Job, ScanHistory


class DatabaseManager:
    """Manages database operations"""

    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            db_path = os.getenv("DATABASE_PATH", "vacai.db")
            database_url = f"sqlite:///{db_path}"

        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def add_job(self, job_data: Dict[str, Any]) -> Job:
        """Add a new job to database"""
        session = self.get_session()
        try:
            # Check if job already exists
            existing = session.query(Job).filter_by(job_url=job_data.get('job_url')).first()
            if existing:
                return existing

            job = Job(**job_data)
            session.add(job)
            session.commit()
            session.refresh(job)
            return job
        finally:
            session.close()

    def update_job_score(self, job_id: int, score_data: Dict[str, Any]):
        """Update job with AI scoring results"""
        session = self.get_session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if job:
                job.ai_score = score_data
                job.overall_score = score_data.get('overall_score')
                job.is_scored = True
                session.commit()
        finally:
            session.close()

    def get_unscored_jobs(self, limit: Optional[int] = None) -> List[Job]:
        """Get jobs that haven't been scored yet"""
        session = self.get_session()
        try:
            query = session.query(Job).filter_by(is_scored=False)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def get_top_jobs(self, limit: int = 20, min_score: float = 70) -> List[Job]:
        """Get top-scored jobs"""
        session = self.get_session()
        try:
            return (
                session.query(Job)
                .filter(Job.is_scored == True, Job.overall_score >= min_score)
                .order_by(desc(Job.overall_score))
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def get_recent_jobs(self, limit: int = 50) -> List[Job]:
        """Get recently scraped jobs"""
        session = self.get_session()
        try:
            return (
                session.query(Job)
                .order_by(desc(Job.scraped_at))
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def record_scan(self, jobs_found: int, jobs_scored: int, search_criteria: Dict) -> ScanHistory:
        """Record a job scan in history"""
        session = self.get_session()
        try:
            scan = ScanHistory(
                jobs_found=jobs_found,
                jobs_scored=jobs_scored,
                search_criteria=search_criteria
            )
            session.add(scan)
            session.commit()
            session.refresh(scan)
            return scan
        finally:
            session.close()

    def get_job_by_url(self, job_url: str) -> Optional[Job]:
        """Get job by URL"""
        session = self.get_session()
        try:
            return session.query(Job).filter_by(job_url=job_url).first()
        finally:
            session.close()

    def mark_applied(self, job_id: int, notes: str = ""):
        """Mark job as applied"""
        session = self.get_session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if job:
                job.is_applied = True
                job.notes = notes
                session.commit()
        finally:
            session.close()

    def bookmark_job(self, job_id: int):
        """Bookmark a job"""
        session = self.get_session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if job:
                job.is_bookmarked = True
                session.commit()
        finally:
            session.close()

    def get_jobs_last_24h(self) -> List[Job]:
        """Get jobs scraped in the last 24 hours"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=24)
            return (
                session.query(Job)
                .filter(Job.scraped_at >= cutoff)
                .order_by(desc(Job.overall_score))
                .all()
            )
        finally:
            session.close()

    def get_jobs_by_date_range(self, hours: int = 24) -> List[Job]:
        """Get jobs from specified time range"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            return (
                session.query(Job)
                .filter(Job.scraped_at >= cutoff)
                .order_by(desc(Job.scraped_at))
                .all()
            )
        finally:
            session.close()

    def cleanup_old_jobs(self, days: int = 30, min_score: float = 60) -> int:
        """Remove old low-scoring jobs to prevent database bloat"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = session.query(Job).filter(
                Job.scraped_at < cutoff,
                Job.overall_score < min_score,
                Job.is_applied == False,
                Job.is_bookmarked == False
            ).delete()
            session.commit()
            return deleted
        finally:
            session.close()

    def get_new_strong_matches(self, hours: int = 24, min_score: float = 80) -> List[Job]:
        """Get new strong matches from recent scans"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            return (
                session.query(Job)
                .filter(
                    Job.scraped_at >= cutoff,
                    Job.overall_score >= min_score,
                    Job.is_scored == True
                )
                .order_by(desc(Job.overall_score))
                .all()
            )
        finally:
            session.close()
