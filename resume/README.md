# Resume Directory

Place your resume file in this directory for VACAI to analyze.

## Supported Formats

- **PDF** (`.pdf`) - Recommended
- **Text** (`.txt`)
- **Markdown** (`.md`)

## Usage

```bash
# Initialize VACAI with your resume
python main.py init --resume resume/your_resume.pdf

# Or with Docker
docker run --rm \
  -v $(pwd)/resume:/app/resume \
  -v $(pwd)/config:/app/config \
  --env-file .env \
  ghcr.io/Neverdecel/vacai:latest \
  python main.py init --resume /app/resume/your_resume.pdf
```

## What Gets Extracted

VACAI analyzes your resume to extract:
- Skills and technologies
- Years of experience
- Preferred job titles/roles
- Work location preferences
- Salary expectations (if mentioned)

This information is saved to `config/search_preferences.yml` and `config/resume_profile.json`.

## Privacy

Your resume is **only used locally** and is **not uploaded** anywhere except to OpenAI's API for analysis. The resume file itself is not stored in version control (`.gitignore` excludes this directory).
