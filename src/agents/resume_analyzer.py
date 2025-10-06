"""Resume analyzer that extracts structured profile and generates search preferences"""

import os
import json
import yaml
import base64
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from openai import OpenAI


class PersonalProfile(BaseModel):
    """Structured resume profile"""
    name: str
    current_role: str
    experience_years: int
    key_skills: List[str] = Field(description="Top 10-15 technical skills")
    soft_skills: List[str] = Field(description="Key soft skills and traits")
    preferred_roles: List[str] = Field(description="Target job titles")
    summary: str = Field(description="2-3 sentence professional summary")


class JobSearchCriteria(BaseModel):
    """Job search parameters for JobSpy"""
    search_terms: List[str] = Field(description="Job titles to search for")
    locations: List[str] = Field(description="Geographic preferences, include 'Remote' if applicable")
    remote_only: bool = False
    job_types: List[str] = Field(default=["fulltime"], description="fulltime, contract, parttime, internship")
    salary_min: Optional[int] = Field(default=None, description="Minimum acceptable salary")
    results_wanted: int = Field(default=50, description="Number of jobs to fetch")
    hours_old: int = Field(default=72, description="Only fetch jobs posted within X hours")


class MatchingPreferences(BaseModel):
    """Preferences for job matching"""
    must_have_skills: List[str] = Field(description="Required skills")
    nice_to_have_skills: List[str] = Field(description="Desired but not required skills")
    company_size_preference: Optional[str] = Field(default=None, description="startup, mid, enterprise, or null")
    industry_preference: Optional[List[str]] = Field(default=None, description="Preferred industries")
    avoid_keywords: List[str] = Field(default=[], description="Red flag keywords in job descriptions")


class SearchPreferences(BaseModel):
    """Complete search preferences generated from resume"""
    personal_profile: PersonalProfile
    job_search_criteria: JobSearchCriteria
    matching_preferences: MatchingPreferences


class ResumeAnalyzer:
    """Analyzes resume and generates structured search preferences"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def analyze_resume_text(self, resume_text: str) -> SearchPreferences:
        """Extract structured profile from resume text"""

        prompt = """Analyze this resume and extract a structured profile for job search automation.

Extract:
1. Personal profile (name, current role, years of experience, skills, preferred roles)
2. Job search criteria (what jobs to search for, locations, remote preference, salary expectations)
3. Matching preferences (must-have vs nice-to-have skills, company preferences)

Be specific and comprehensive. For skills, prioritize technical/hard skills.
For search terms, include role variations (e.g., "Senior Software Engineer", "Staff Engineer").
For locations, include "Remote" if the candidate seems open to remote work.

Resume:
""" + resume_text

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "user", "content": prompt}],
            response_format=SearchPreferences,
        )

        return response.choices[0].message.parsed

    def analyze_resume_pdf(self, pdf_path: str) -> SearchPreferences:
        """Extract structured profile from PDF resume using vision"""

        # Read PDF and encode as base64
        with open(pdf_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')

        # Note: OpenAI doesn't directly support PDF in vision API
        # We'll use a workaround: ask user to convert PDF to images
        # OR use a PDF extraction library

        # Let's use PyPDF2 for text extraction instead
        try:
            import PyPDF2

            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                resume_text = ""
                for page in pdf_reader.pages:
                    resume_text += page.extract_text() + "\n"

            return self.analyze_resume_text(resume_text)

        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF support. Install with: pip install PyPDF2"
            )

    def save_to_yaml(self, preferences: SearchPreferences, output_path: str = "config/search_preferences.yml"):
        """Save preferences to YAML file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save as YAML
        with open(output_file, 'w') as f:
            yaml.dump(
                preferences.model_dump(exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False
            )

        return output_file

    def save_profile_json(self, preferences: SearchPreferences, output_path: str = "config/resume_profile.json"):
        """Save personal profile as JSON for job scoring"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(preferences.model_dump(), f, indent=2)

        return output_file


def analyze_resume_file(resume_path: str, output_dir: str = "config") -> SearchPreferences:
    """Convenience function to analyze resume from file"""

    resume_path = Path(resume_path)
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume not found: {resume_path}")

    # Initialize analyzer
    analyzer = ResumeAnalyzer()

    # Handle different file types
    if resume_path.suffix.lower() == '.pdf':
        print("📄 Extracting text from PDF...")
        preferences = analyzer.analyze_resume_pdf(str(resume_path))
    elif resume_path.suffix.lower() in ['.txt', '.md']:
        resume_text = resume_path.read_text()
        preferences = analyzer.analyze_resume_text(resume_text)
    else:
        raise ValueError(f"Unsupported file type: {resume_path.suffix}. Use .pdf, .txt, or .md")

    # Save outputs
    yaml_path = analyzer.save_to_yaml(preferences, f"{output_dir}/search_preferences.yml")
    json_path = analyzer.save_profile_json(preferences, f"{output_dir}/resume_profile.json")

    print(f"✓ Resume analyzed successfully")
    print(f"✓ Search preferences saved to: {yaml_path}")
    print(f"✓ Profile JSON saved to: {json_path}")

    return preferences
