# VACAI Quick Start Guide

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Setup environment:**
```bash
cp config/.env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-proj-...
```

## Usage

### 1. Initialize with Your Resume

First, analyze your resume to generate search preferences:

```bash
python main.py init --resume /path/to/your/resume.txt
```

This will:
- Extract your skills, experience, and preferences using AI
- Generate `config/search_preferences.yml` (JobSpy parameters)
- Generate `config/resume_profile.json` (for job scoring)

**Note:** Supports PDF (.pdf), plain text (.txt), and markdown (.md) resumes. PDF parsing is automatic via PyPDF2.

### 2. Scan for Jobs

Scrape jobs from multiple platforms and score them:

```bash
python main.py scan
```

This will:
- Scrape jobs from LinkedIn, Indeed, Glassdoor (based on your preferences)
- Score each job with a single AI call (token-efficient)
- Store results in SQLite database

Optional: Limit number of jobs to score:
```bash
python main.py scan --max-jobs 50
```

### 3. View Results

See your top job matches:

```bash
python main.py report
```

Customize the report:
```bash
python main.py report --min-score 80 --limit 10
```

View details of a specific job:
```bash
python main.py show 1  # Show job #1 from the report
```

### 4. Check Statistics

```bash
python main.py stats
```

## Workflow Example

```bash
# One-time setup
python main.py init --resume ~/Documents/resume.txt

# Daily job scan
python main.py scan

# Review matches
python main.py report --min-score 75

# View top match details
python main.py show 1
```

## Configuration

### Customize Search Preferences

After running `init`, you can manually edit `config/search_preferences.yml`:

```yaml
job_search_criteria:
  search_terms:
    - "Senior Software Engineer"
    - "Machine Learning Engineer"
  locations:
    - "Remote"
    - "San Francisco, CA"
  remote_only: true
  results_wanted: 100
  hours_old: 72
```

### Adjust Job Boards

Edit `.env` to change which platforms to scrape:

```bash
JOB_BOARDS=linkedin,indeed,glassdoor
```

Available: `linkedin`, `indeed`, `zip_recruiter`, `glassdoor`, `google`

## Understanding Scores

Jobs are scored on 5 dimensions (0-100):
- **Skills Match**: How well your skills align with requirements
- **Experience Fit**: Seniority and experience level match
- **Salary Alignment**: Compensation expectations
- **Culture Fit**: Company values and environment
- **Growth Potential**: Learning and advancement opportunities

**Overall Score**:
- 80-100: Strong match (worth applying)
- 60-79: Potential match (review carefully)
- 0-59: Pass (likely not a good fit)

## Token Efficiency

- ~300-500 tokens per job using GPT-4o-mini
- 100 jobs ≈ 50K tokens ≈ **$0.01-0.02 per scan**
- Single AI agent design (vs multi-agent approaches)
- Resume analysis (one-time): ~2K tokens ≈ **$0.01-0.05**

## Troubleshooting

**No jobs found:**
- Check your `search_preferences.yml` search terms
- Try broader locations or keywords
- Increase `results_wanted` limit

**JobSpy errors:**
- Some platforms (esp. LinkedIn) may require proxies
- Try removing problematic platforms from `JOB_BOARDS`

**API errors:**
- Verify your `OPENAI_API_KEY` in `.env`
- Check your API quota/billing at platform.openai.com

## Next Steps

1. Set up a cron job for daily scans:
```bash
0 9 * * * cd /home/neverdecel/code/vacai && python main.py scan && python main.py report
```

2. Export top matches to apply:
```bash
python main.py report --min-score 85 > top_jobs.txt
```

3. Track applications by bookmarking jobs in the database
