"""Single AI agent for holistic job scoring - token-efficient design"""

import os
import json
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from openai import OpenAI


class JobScore(BaseModel):
    """Structured output for job scoring"""

    overall_score: int = Field(ge=0, le=100, description="Overall match score 0-100")

    # Dimension scores
    skills_match: int = Field(ge=0, le=100, description="How well candidate's skills match job requirements")
    experience_fit: int = Field(ge=0, le=100, description="Experience level alignment")
    salary_alignment: int = Field(ge=0, le=100, description="Salary expectations vs offer")
    culture_fit: int = Field(ge=0, le=100, description="Company culture and values match")
    growth_potential: int = Field(ge=0, le=100, description="Career growth opportunities")
    commute_feasibility: int = Field(ge=0, le=100, description="Commute distance and work mode alignment (hybrid/remote preferred)")
    employment_type_fit: int = Field(ge=0, le=100, description="In-house vs consultancy (CRITICAL: only in-house positions)")

    # Qualitative analysis
    match_highlights: List[str] = Field(description="Top 3-5 reasons this job is a good match")
    concerns: List[str] = Field(description="Top 3-5 concerns or red flags")

    # Decision
    decision: str = Field(
        description="strong_match (>80), potential (60-80), or pass (<60)"
    )

    # Brief summary
    summary: str = Field(description="2-3 sentence overall assessment")


class JobScorer:
    """Single AI agent that scores jobs holistically"""

    def __init__(self, profile_path: str = "config/resume_profile.json", api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.profile = self._load_profile(profile_path)
        self.profile_summary = self._create_profile_summary()

    def _load_profile(self, profile_path: str) -> dict:
        """Load candidate profile from JSON"""
        path = Path(profile_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Resume profile not found at {profile_path}. "
                "Run 'vacai init' first to analyze your resume."
            )

        with open(path, 'r') as f:
            return json.load(f)

    def _create_profile_summary(self) -> str:
        """Create concise profile summary for prompts"""
        personal = self.profile['personal_profile']
        matching = self.profile['matching_preferences']

        summary = f"""Candidate Profile:
- Name: {personal['name']}
- Current Role: {personal['current_role']}
- Experience: {personal['experience_years']} years
- Key Skills: {', '.join(personal['key_skills'][:10])}
- Target Roles: {', '.join(personal['preferred_roles'])}
- Must-Have Skills: {', '.join(matching['must_have_skills'])}
- Nice-to-Have: {', '.join(matching['nice_to_have_skills'][:5])}
- Professional Summary: {personal['summary']}
"""

        # Add salary if available
        criteria = self.profile['job_search_criteria']
        if criteria.get('salary_min'):
            summary += f"- Minimum Salary: ${criteria['salary_min']:,}\n"

        # Add commute and work mode preferences
        if criteria.get('home_location'):
            summary += f"- Home Location: {criteria['home_location']}\n"
        if criteria.get('max_commute_minutes'):
            summary += f"- Maximum Commute: {criteria['max_commute_minutes']} minutes\n"
        if criteria.get('preferred_work_mode'):
            summary += f"- Preferred Work Mode: {criteria['preferred_work_mode']}\n"
            summary += f"- Acceptable Locations (within 30min): Haarlem, Amsterdam, Leiden, Hoofddorp, or Remote/Hybrid\n"

        # Add employment type preference
        if matching.get('employment_type_preference'):
            summary += f"- Employment Type: {matching['employment_type_preference']} ONLY (no consultancy/detachering)\n"

        return summary

    def score_job(
        self,
        job_title: str,
        company: str,
        job_description: str,
        salary_range: Optional[str] = None,
        location: Optional[str] = None
    ) -> JobScore:
        """Score a single job posting"""

        # Build job context
        job_context = f"""Job Title: {job_title}
Company: {company}"""

        if location:
            job_context += f"\nLocation: {location}"
        if salary_range:
            job_context += f"\nSalary: {salary_range}"

        job_context += f"\n\nJob Description:\n{job_description[:4000]}"  # Limit description length

        # Create scoring prompt
        prompt = f"""{self.profile_summary}

Evaluate this job posting for the candidate:

{job_context}

Provide a comprehensive evaluation scoring the following dimensions (0-100):
1. Skills Match: How well do the candidate's skills match the requirements?
2. Experience Fit: Does the seniority level and experience align?
3. Salary Alignment: Is the compensation appropriate? (100 if unknown)
4. Culture Fit: Based on company description and role, does it match candidate preferences?
5. Growth Potential: Opportunities for learning and career advancement?
6. Commute Feasibility: Evaluate based on:
   - Job in Haarlem, Amsterdam, Leiden, or Hoofddorp = 100 (within 30min commute)
   - Remote or Hybrid = 100 (preferred work mode)
   - Fully on-site outside these cities = 20-40 (penalize heavily)
   - Look for keywords: "hybrid", "remote", "flexible", "home office"
   - Penalize: "5 days office", "fully on-site", "no remote"
7. Employment Type Fit: Is this an IN-HOUSE position? (CRITICAL - MUST BE 100 or 0-20)

   **STEP-BY-STEP LINGUISTIC ANALYSIS** (analyze the job description carefully):

   **STEP 1: Preposition Analysis (Dutch & English)**
   Check how "klanten/clients" is used in context:

   🚩 CONSULTANCY indicators (Score 0-20):
   - Dutch: "bij klanten" (at clients), "bij onze klanten" (at our clients), "op locatie bij", "je werkt bij"
   - English: "at our clients", "at client sites", "at clients'", "you will work at"
   - If description says you work **AT/BIJ** clients → CONSULTANCY → Score 0-20

   ✅ IN-HOUSE indicators (Score 100):
   - Dutch: "voor klanten bouwen we" (we build for customers), "met klanten werken" (work with customers)
   - English: "we build for clients", "serving our customers", "working with clients"
   - If description says you build/serve customers but work at own office → IN-HOUSE → Score 100

   **STEP 2: Work Location Analysis**
   Where does the actual work happen?

   🚩 CONSULTANCY (0-20):
   - "op klantlocatie" (at client location)
   - "op projectbasis bij verschillende" (project-based at various)
   - "je wordt ingezet bij" (you are deployed at)
   - "at client premises", "on-site at client"

   ✅ IN-HOUSE (100):
   - "op ons kantoor" (at our office)
   - "remote/thuiswerken" (remote/work from home)
   - "in ons team" (in our team)
   - "at our headquarters", "from our office"

   **STEP 3: Product/Project Ownership**
   Whose product or project are you working on?

   🚩 CONSULTANCY (0-20):
   - "klantprojecten" (client projects)
   - "projecten voor opdrachtgevers" (projects for clients)
   - "deployed to client projects"

   ✅ IN-HOUSE (100):
   - "ons eigen product" (our own product)
   - "ons platform" (our platform)
   - "voor ons bedrijf" (for our company)
   - "our product", "our platform", "our internal systems"

   **STEP 4: Explicit Red Flags**
   🚩 Automatic 0-20 if found:
   - "detachering", "uitzenden", "inhuur" (staffing/temp work)
   - "consultancy", "secondment", "contracting", "staffing"

   **FINAL DECISION RULE (BE PRECISE - NO ASSUMPTIONS):**

   Score 0-20 ONLY if you find EXPLICIT evidence:
   - ✓ "bij klanten", "bij onze klanten", "at clients", "at our clients"
   - ✓ "op klantlocatie", "at client site", "client premises"
   - ✓ "wordt ingezet bij", "deployed to clients"
   - ✓ "detachering", "secondment", "staffing", "uitzenden"

   Score 100 if:
   - ✓ "ons team", "our team", "ons product", "our platform"
   - ✓ "in-house", "internal", "eigen team"
   - ✓ No consultancy indicators found

   **CRITICAL: Do NOT infer consultancy from:**
   - ❌ Company name (many large companies have in-house AND consultancy divisions)
   - ❌ The word "projects" (in-house teams also work on projects!)
   - ❌ The word "klanten" alone (serving customers ≠ working at clients)
   - ❌ Industry assumptions (banks, tech companies have in-house engineers!)

   **DEFAULT TO IN-HOUSE (100) unless you find EXPLICIT consultancy language in the description**

Also provide:
- Overall Score (weighted average: skills 25%, experience 20%, employment_type 25%, commute 15%, culture 10%, growth 5%)
- Match Highlights (3-5 specific reasons this is a good fit)
- Concerns (3-5 red flags or areas of mismatch, FLAG ANY CONSULTANCY INDICATORS)
- Decision (strong_match, potential, or pass)
- Summary (brief 2-3 sentence assessment)

Be honest and critical. A score of 60-70 is average, 80+ is excellent.

CRITICAL: Use linguistic analysis, NOT company blacklists!

Analyze the job description using the 4-step process above:
1. Check prepositions: "bij" (at) vs "voor" (for) vs "met" (with)
2. Identify work location: client site vs own office
3. Determine ownership: client projects vs own product
4. Look for explicit staffing/consultancy terms

Common mistakes to avoid:
❌ Don't reject based on "klanten" alone - context matters!
❌ Don't assume company name indicates consultancy - analyze the role description
✅ DO look for "bij klanten", "at clients", "op klantlocatie"
✅ DO check if they say "ons product" or "client projects"
"""

        # Use OpenAI structured output
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",  # Using mini for cost efficiency
                messages=[{"role": "user", "content": prompt}],
                response_format=JobScore,
            )

            return response.choices[0].message.parsed

        except Exception as e:
            # Fallback in case of error
            print(f"⚠ Error scoring job: {str(e)}")
            return JobScore(
                overall_score=0,
                skills_match=0,
                experience_fit=0,
                salary_alignment=0,
                culture_fit=0,
                growth_potential=0,
                match_highlights=["Error during scoring"],
                concerns=[str(e)],
                decision="pass",
                summary="Failed to score this job due to an error."
            )


def is_consultancy_job(description: str) -> tuple[bool, str]:
    """
    Deterministic check for consultancy indicators BEFORE AI scoring.
    Returns (is_consultancy, reason)
    """
    if not description:
        return False, ""

    desc_lower = description.lower()

    # Explicit consultancy phrases (Dutch & English)
    consultancy_patterns = [
        ("bij onze klanten", "works at our clients"),
        ("bij klanten", "works at clients"),
        ("op locatie bij klanten", "on-site at clients"),
        ("bij de klant", "at the client"),
        ("op klantlocatie", "at client location"),
        ("wordt ingezet bij", "deployed at"),
        ("at our clients", "at our clients"),
        ("at client sites", "at client sites"),
        ("at client premises", "at client premises"),
        ("detachering", "secondment/staffing"),
        ("uitzenden", "temp staffing"),
        ("inhuur", "contractor placement"),
    ]

    for pattern, reason in consultancy_patterns:
        if pattern in desc_lower:
            return True, f"Found '{pattern}' ({reason})"

    return False, ""


def score_job_from_db(job, scorer: JobScorer) -> dict:
    """Score a job from database object"""

    # DETERMINISTIC PRE-FILTER: Check for consultancy indicators
    is_consultancy, consultancy_reason = is_consultancy_job(job.description)

    # Format salary range
    salary_range = None
    if job.min_salary or job.max_salary:
        if job.min_salary and job.max_salary:
            salary_range = f"${job.min_salary:,.0f} - ${job.max_salary:,.0f}"
        elif job.min_salary:
            salary_range = f"${job.min_salary:,.0f}+"
        else:
            salary_range = f"Up to ${job.max_salary:,.0f}"

    # Score the job
    score = scorer.score_job(
        job_title=job.title,
        company=job.company,
        job_description=job.description or "",
        salary_range=salary_range,
        location=job.location
    )

    score_dict = score.model_dump()

    # OVERRIDE: If deterministic check found consultancy, force employment_type to 0
    if is_consultancy:
        score_dict['employment_type_fit'] = 0
        # Add to concerns if not already mentioned
        consultancy_concern = f"❌ CONSULTANCY DETECTED: {consultancy_reason}"
        if 'concerns' in score_dict and consultancy_concern not in score_dict.get('concerns', []):
            score_dict['concerns'].insert(0, consultancy_concern)

    # CRITICAL FIX: Calculate overall_score ourselves (AI doesn't follow weights correctly)
    # Weights: skills 25%, experience 20%, employment_type 25%, commute 15%, culture 10%, growth 5%
    calculated_overall = int(
        score_dict['skills_match'] * 0.25 +
        score_dict['experience_fit'] * 0.20 +
        score_dict['employment_type_fit'] * 0.25 +
        score_dict['commute_feasibility'] * 0.15 +
        score_dict['culture_fit'] * 0.10 +
        score_dict['growth_potential'] * 0.05
    )

    # CRITICAL: Hard rejection for consultancy (employment_type < 30)
    # User requirement: "absolute must for me is an in-house position"
    if score_dict['employment_type_fit'] < 30:
        # Consultancy detected - automatic rejection
        score_dict['overall_score'] = min(calculated_overall, 25)  # Cap at 25 max
        score_dict['decision'] = 'pass'
        # Add rejection note to concerns if not already there
        if 'concerns' in score_dict and score_dict['concerns']:
            consultancy_concern = any('consultancy' in str(c).lower() or 'klanten' in str(c).lower()
                                     for c in score_dict['concerns'])
            if not consultancy_concern:
                score_dict['concerns'].insert(0, "❌ REJECTED: Consultancy/detachering role (employment_type < 30)")
    else:
        # Normal scoring
        score_dict['overall_score'] = calculated_overall

        # Update decision based on correct score
        if calculated_overall >= 80:
            score_dict['decision'] = 'strong_match'
        elif calculated_overall >= 60:
            score_dict['decision'] = 'potential'
        else:
            score_dict['decision'] = 'pass'

    return score_dict


def batch_score_jobs(db_manager, max_jobs: Optional[int] = None) -> int:
    """Score all unscored jobs in database"""

    scorer = JobScorer()

    # Get unscored jobs
    unscored = db_manager.get_unscored_jobs(limit=max_jobs)

    if not unscored:
        print("✓ All jobs already scored")
        return 0

    # Filter out jobs without descriptions
    jobs_with_desc = [j for j in unscored if j.description and len(j.description.strip()) > 0]
    skipped = len(unscored) - len(jobs_with_desc)

    if skipped > 0:
        print(f"⚠️  Skipping {skipped} job(s) without descriptions (can't score accurately)")

    if not jobs_with_desc:
        print("❌ No jobs with descriptions to score")
        return 0

    print(f"🤖 Scoring {len(jobs_with_desc)} jobs with AI...")

    scored_count = 0
    for i, job in enumerate(jobs_with_desc, 1):
        print(f"  [{i}/{len(jobs_with_desc)}] Scoring: {job.title} at {job.company}")

        try:
            score_data = score_job_from_db(job, scorer)
            db_manager.update_job_score(job.id, score_data)
            scored_count += 1

            # Show score
            overall = score_data['overall_score']
            decision = score_data['decision']
            print(f"    → Score: {overall}/100 ({decision})")

        except Exception as e:
            print(f"    ✗ Error: {str(e)}")

    print(f"\n✓ Scored {scored_count} jobs")

    return scored_count
