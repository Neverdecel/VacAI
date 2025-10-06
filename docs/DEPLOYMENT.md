# VacAI Deployment Guide

This guide covers deploying VacAI using Docker and GitHub Container Registry (GHCR).

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key
- GitHub account for GHCR access

### 1. Pull the Latest Image

```bash
# Replace Neverdecel with the repository owner
docker pull ghcr.io/Neverdecel/vacai:latest
```

### 2. Create Local Directories

```bash
mkdir -p data reports logs config resume
```

### 3. Set Up Environment Variables

Create a `.env` file:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional - Telegram Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database
DATABASE_PATH=/app/data/vacai.db
```

### 4. Run with Docker Compose

```bash
# Start the container
docker-compose up -d

# Initialize with your resume
docker-compose exec vacai python main.py init --resume /app/resume/your_resume.pdf

# Run a job scan
docker-compose exec vacai python main.py scan

# Generate a report
docker-compose exec vacai python main.py report
```

## Running Directly with Docker

### Initialize
```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/resume:/app/resume \
  --env-file .env \
  ghcr.io/Neverdecel/vacai:latest \
  python main.py init --resume /app/resume/resume.pdf
```

### Run Job Scan
```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/reports:/app/reports \
  --env-file .env \
  ghcr.io/Neverdecel/vacai:latest \
  python main.py scan
```

### Generate Report
```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  --env-file .env \
  ghcr.io/Neverdecel/vacai:latest \
  python main.py report
```

## Scheduled Daily Scans

### Option 1: Host Cron Job

Add to your crontab (`crontab -e`):

```bash
# Run VacAI scan daily at 9 AM
0 9 * * * cd /path/to/vacai && docker-compose exec -T vacai python main.py scan && docker-compose exec -T vacai python -c "from src.database.manager import DatabaseManager; from src.notifier.telegram_notifier import send_daily_report_sync; db = DatabaseManager(); jobs = db.get_jobs_last_24h(); strong = [j for j in jobs if j.overall_score >= 80]; potential = [j for j in jobs if 60 <= j.overall_score < 80]; send_daily_report_sync(strong, potential, len(jobs))" >> /path/to/vacai/logs/cron.log 2>&1
```

### Option 2: Docker with Host Cron Script

Create `docker-scan.sh`:

```bash
#!/bin/bash
cd /path/to/vacai
docker-compose exec -T vacai python main.py scan
docker-compose exec -T vacai python main.py report
```

Make it executable and add to cron:
```bash
chmod +x docker-scan.sh
echo "0 9 * * * /path/to/vacai/docker-scan.sh" | crontab -
```

## GitHub Container Registry (GHCR) Details

### Image Tags

- `ghcr.io/Neverdecel/vacai:latest` - Latest main branch build
- `ghcr.io/Neverdecel/vacai:main` - Main branch
- `ghcr.io/Neverdecel/vacai:v1.0.0` - Specific version tag
- `ghcr.io/Neverdecel/vacai:main-abc1234` - Commit SHA

### Pulling Images

For public images:
```bash
docker pull ghcr.io/Neverdecel/vacai:latest
```

For private images (requires authentication):
```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull image
docker pull ghcr.io/Neverdecel/vacai:latest
```

### Building Images Locally

```bash
# Build the image
docker build -t vacai:local .

# Test it
docker run --rm vacai:local python --version
```

## CI/CD Pipeline

### Automatic Builds

Images are automatically built and pushed to GHCR when:
- Code is pushed to `main` branch
- Version tags are created (e.g., `v1.0.0`)
- Manual workflow trigger

### PR Validation

All pull requests are automatically validated:
- Docker image builds successfully
- Code formatting checks (Black, isort)
- Linting checks (Flake8)
- Basic import tests

## Volume Mounts

| Volume | Purpose | Required |
|--------|---------|----------|
| `/app/data` | SQLite database storage | Yes |
| `/app/config` | Configuration files | Yes |
| `/app/reports` | Generated reports | Recommended |
| `/app/logs` | Application logs | Recommended |
| `/app/resume` | Resume files | For init only |

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-4o-mini` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | No | - |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | No | - |
| `DATABASE_PATH` | Database file path | No | `/app/data/vacai.db` |

## Health Checks

The container includes a health check that verifies database connectivity:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' vacai
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs vacai

# Verify environment variables
docker-compose config
```

### Permission Issues
```bash
# Ensure local directories are writable
chmod -R 755 data reports logs config
```

### Database Locked
```bash
# Stop container and remove lock
docker-compose down
rm -f data/vacai.db-journal
docker-compose up -d
```

### Image Pull Issues
```bash
# Authenticate with GHCR
gh auth token | docker login ghcr.io -u USERNAME --password-stdin

# Or use personal access token
echo $PAT | docker login ghcr.io -u USERNAME --password-stdin
```

## Production Recommendations

1. **Use specific version tags** instead of `latest` for stability
2. **Set up log rotation** for container logs
3. **Monitor disk usage** for database and reports
4. **Use secrets management** for API keys (don't commit .env)
5. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

## Security Best Practices

- Container runs as non-root user (`vacai`)
- Minimal base image (python:3.10-slim)
- No sensitive data in image layers
- Environment variables for secrets
- Read-only volume mounts where appropriate

## Updating

```bash
# Pull latest image
docker-compose pull

# Restart with new image
docker-compose up -d

# Verify version
docker-compose exec vacai python main.py --version
```

## Backup

```bash
# Backup database
cp data/vacai.db data/vacai_backup_$(date +%Y%m%d).db

# Backup entire data directory
tar -czf vacai_backup_$(date +%Y%m%d).tar.gz data/ config/ reports/
```

## Support

- GitHub Issues: Submit issues in your forked repository
- Documentation: See README.md and other docs in repository
