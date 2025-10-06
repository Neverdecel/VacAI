# VACAI - AI-Powered Job Search Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-available-blue.svg)](https://github.com/features/packages)

Automate your job search with AI-powered job matching and scoring. VACAI analyzes your resume, scrapes job listings from multiple platforms, and scores each position based on your skills and preferences.

## Features

- 🤖 **AI Resume Analysis**: Automatically extract your skills and preferences using OpenAI GPT-4
- 📄 **PDF Support**: Direct PDF resume parsing (also supports .txt and .md)
- 🔍 **Multi-Platform Scraping**: Search across LinkedIn, Indeed, Glassdoor, and more
- 📊 **Smart Scoring**: Single AI agent scores jobs holistically (token-efficient)
- 📈 **Daily Reports**: Get ranked job matches delivered automatically
- 📱 **Telegram Integration**: Receive daily reports with clickable "Apply" links directly in Telegram

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Pull the latest image (replace Neverdecel with the repo owner)
docker pull ghcr.io/Neverdecel/vacai:latest

# Create directories and .env file
mkdir -p data reports logs config resume
cp config/.env.example .env
# Edit .env and add your OPENAI_API_KEY

# Initialize with your resume
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/resume:/app/resume \
  --env-file .env \
  ghcr.io/Neverdecel/vacai:latest \
  python main.py init --resume /app/resume/your_resume.pdf

# Run a scan
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/reports:/app/reports \
  --env-file .env \
  ghcr.io/Neverdecel/vacai:latest \
  python main.py scan

# Or use docker-compose
docker-compose up -d
docker-compose exec vacai python main.py scan
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full Docker deployment guide.

### Option 2: Local Installation

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Setup configuration**
```bash
cp config/.env.example .env
# Add your OPENAI_API_KEY
```

3. **Initialize with your resume**
```bash
python main.py init --resume path/to/resume.pdf
```

4. **Run job scan**
```bash
python main.py scan
```

5. **View results**
```bash
python main.py report
```

6. **Setup Telegram notifications** (optional)
```bash
# See TELEGRAM_SETUP.md for detailed instructions
python main.py test-telegram
```

## How It Works

1. **Analyze Resume**: AI extracts your skills and preferences from your resume
2. **Scrape Jobs**: Automatically searches LinkedIn, Indeed, Glassdoor, etc.
3. **Score & Rank**: AI evaluates each job against your profile
4. **Daily Reports**: Get ranked results with scores and reasoning
5. **Notifications**: Optional Telegram integration for daily updates

## Architecture

- **Single AI Agent**: One OpenAI API call per job for efficient token usage
- **JobSpy Integration**: Scrapes jobs from multiple platforms
- **SQLite Database**: Stores jobs and scores locally
- **Structured Output**: Pydantic models ensure consistent scoring
- **PDF Support**: PyPDF2 for resume text extraction

## Cost Estimate

- ~100 jobs × 500 tokens = 50K tokens per scan
- Using GPT-4o-mini: ~$0.01-0.02 per scan
- Using GPT-4o: ~$0.25 per scan
- Resume analysis (one-time): ~$0.01-0.05

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: See `/docs` folder for detailed guides
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

## Deployment

### Docker & GHCR

VacAI is available as a Docker image on GitHub Container Registry:

```bash
docker pull ghcr.io/neverdecel/vacai:latest
```

**Available tags:**
- `latest` - Latest stable release
- `main` - Main branch builds
- `v1.0.0` - Specific version tags

**Quick deploy with docker-compose:**
```bash
docker-compose up -d
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for comprehensive deployment guide including:
- Docker setup and configuration
- GHCR image usage
- Scheduled scans with cron
- Production best practices
- Health checks and monitoring

### CI/CD

Automated builds on:
- Push to `main` branch
- Version tag releases
- Pull request validation

Images are automatically built for `linux/amd64` and `linux/arm64` platforms.
