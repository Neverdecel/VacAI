"""Job scraper using JobSpy library"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from jobspy import scrape_jobs
import pandas as pd


class JobScraper:
    """Scrapes jobs using JobSpy based on search preferences"""

    def __init__(self, preferences_path: str = "config/search_preferences.yml"):
        self.preferences_path = Path(preferences_path)
        self.preferences = self._load_preferences()

    def _load_preferences(self) -> Dict[str, Any]:
        """Load search preferences from YAML"""
        if not self.preferences_path.exists():
            raise FileNotFoundError(
                f"Search preferences not found at {self.preferences_path}. "
                "Run 'vacai init' first to analyze your resume."
            )

        with open(self.preferences_path, 'r') as f:
            return yaml.safe_load(f)

    def scrape(self, max_results: Optional[int] = None) -> pd.DataFrame:
        """Scrape jobs based on preferences"""

        criteria = self.preferences['job_search_criteria']
        search_terms = criteria.get('search_terms', [])
        locations = criteria.get('locations', ['Remote'])

        # Get job board list from env or use defaults
        job_boards_str = os.getenv('JOB_BOARDS', 'linkedin,indeed,glassdoor')
        job_boards = [board.strip() for board in job_boards_str.split(',')]

        results_wanted = max_results or criteria.get('results_wanted', 50)
        hours_old = criteria.get('hours_old', 72)

        # JobSpy supports: linkedin, indeed, zip_recruiter, glassdoor, google
        all_jobs = []

        for search_term in search_terms:
            for location in locations:
                print(f"🔍 Scraping: {search_term} in {location}")

                try:
                    jobs_df = scrape_jobs(
                        site_name=job_boards,
                        search_term=search_term,
                        location=location,
                        results_wanted=results_wanted // len(search_terms),  # Distribute quota
                        hours_old=hours_old,
                        country_indeed='Netherlands',  # NL-based jobs only
                        linkedin_fetch_description=True  # CRITICAL: Fetch full LinkedIn descriptions
                    )

                    if jobs_df is not None and not jobs_df.empty:
                        all_jobs.append(jobs_df)
                        print(f"  ✓ Found {len(jobs_df)} jobs")
                    else:
                        print(f"  ⚠ No jobs found")

                except Exception as e:
                    print(f"  ✗ Error scraping: {str(e)}")

        # Combine all results
        if all_jobs:
            combined_df = pd.concat(all_jobs, ignore_index=True)
            # Remove duplicates based on job_url
            combined_df = combined_df.drop_duplicates(subset=['job_url'], keep='first')
            return combined_df
        else:
            return pd.DataFrame()

    def format_for_database(self, jobs_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert JobSpy DataFrame to database-ready format"""

        job_records = []

        for _, row in jobs_df.iterrows():
            job_data = {
                'job_url': row.get('job_url'),
                'title': row.get('title'),
                'company': row.get('company'),
                'location': row.get('location'),
                'job_type': row.get('job_type'),
                'is_remote': self._is_remote(row),
                'description': row.get('description'),
                'min_salary': self._extract_salary(row, 'min'),
                'max_salary': self._extract_salary(row, 'max'),
                'salary_currency': row.get('currency', 'USD'),
                'source': row.get('site'),
                'posted_date': self._parse_date(row.get('date_posted')),
                'scraped_at': datetime.utcnow()
            }

            # Only add jobs with valid URLs
            if job_data['job_url']:
                job_records.append(job_data)

        return job_records

    def _is_remote(self, row: pd.Series) -> bool:
        """Determine if job is remote"""
        location = str(row.get('location', '')).lower()
        is_remote = row.get('is_remote', False)
        return is_remote or 'remote' in location

    def _extract_salary(self, row: pd.Series, min_or_max: str) -> Optional[float]:
        """Extract min or max salary"""
        try:
            if min_or_max == 'min':
                return float(row.get('min_amount', 0)) if pd.notna(row.get('min_amount')) else None
            else:
                return float(row.get('max_amount', 0)) if pd.notna(row.get('max_amount')) else None
        except (ValueError, TypeError):
            return None

    def _parse_date(self, date_value) -> Optional[datetime]:
        """Parse date from various formats"""
        if pd.isna(date_value):
            return None

        try:
            if isinstance(date_value, datetime):
                return date_value
            elif isinstance(date_value, str):
                return pd.to_datetime(date_value)
            else:
                return None
        except Exception:
            return None


def scrape_and_save(db_manager, preferences_path: str = "config/search_preferences.yml") -> int:
    """Scrape jobs and save to database"""

    scraper = JobScraper(preferences_path)

    print("🚀 Starting job scrape...")
    jobs_df = scraper.scrape()

    if jobs_df.empty:
        print("❌ No jobs found")
        return 0

    print(f"\n✓ Found {len(jobs_df)} total jobs")

    # Format for database
    job_records = scraper.format_for_database(jobs_df)
    print(f"✓ Prepared {len(job_records)} jobs for database")

    # Save to database
    saved_count = 0
    for job_data in job_records:
        try:
            db_manager.add_job(job_data)
            saved_count += 1
        except Exception as e:
            print(f"⚠ Error saving job: {str(e)}")

    print(f"✓ Saved {saved_count} new jobs to database")

    return saved_count
