# VACAI - Daily Automation Setup

This guide will help you set up automated daily job scanning with VACAI.

## Overview

VACAI can run automatically every day to:
1. Scrape new job postings
2. Score them with AI (only new jobs, no duplicates)
3. Generate a daily report highlighting strong matches
4. Clean up old low-scoring jobs weekly

## Setup Instructions

### 1. Make Scripts Executable

```bash
chmod +x /home/neverdecel/code/vacai/daily_scan.sh
chmod +x /home/neverdecel/code/vacai/cleanup.sh
```

### 2. Set Up Cron Jobs

Open your crontab:
```bash
crontab -e
```

Add these entries:

```bash
# VACAI Daily Job Scan - Runs every day at 9:00 AM
0 9 * * * /home/neverdecel/code/vacai/daily_scan.sh

# VACAI Weekly Cleanup - Runs every Sunday at 3:00 AM
0 3 * * 0 /home/neverdecel/code/vacai/cleanup.sh
```

### 3. Alternative: Run Manually

You can also run the commands manually:

**Daily scan (incremental):**
```bash
cd /home/neverdecel/code/vacai
source venv/bin/activate
python main.py daily
```

**Weekly cleanup:**
```bash
cd /home/neverdecel/code/vacai
source venv/bin/activate
python main.py cleanup --days 30 --min-score 60
```

## CLI Commands

VACAI provides the following commands:

### Daily Operations

```bash
# Run daily incremental scan (only new jobs)
python main.py daily

# Run full scan (all jobs, no incremental)
python main.py scan

# Clean up old low-scoring jobs
python main.py cleanup --days 30 --min-score 60
```

### Reporting & Analysis

```bash
# Show database statistics
python main.py stats

# Generate comprehensive report
python main.py report --min-score 70 --limit 20

# Show detailed job information
python main.py show <job_number>
```

## How Daily Automation Works

### Incremental Processing

VACAI is designed for daily automation with intelligent duplicate detection:

1. **Duplicate Prevention**: Each job is tracked by URL, so the same job is never added twice
2. **Incremental Scoring**: Only unscored jobs are processed (saves API costs)
3. **Daily Reports**: Highlights NEW jobs found in last 24 hours
4. **Automatic Cleanup**: Removes old low-scoring jobs to prevent database bloat

### What Happens During Daily Run

```
Daily Scan (9:00 AM)
├── Scrape job boards (LinkedIn, Indeed, Glassdoor)
│   └── Only new jobs are added to database
├── Score unscored jobs with AI
│   └── Only processes jobs that haven't been scored yet
└── Generate daily report
    └── Shows new strong matches (80+) and potential matches (60-79)

Weekly Cleanup (Sunday 3:00 AM)
└── Remove jobs older than 30 days with score < 60
    └── Preserves jobs you applied to or bookmarked
```

## Logs

All automation logs are stored in `/home/neverdecel/code/vacai/logs/`:

- `daily_scan_YYYYMMDD.log` - Daily scan logs (kept for 30 days)
- `cleanup_YYYYMMDD.log` - Weekly cleanup logs (kept for 90 days)

View recent logs:
```bash
# View today's scan log
tail -f /home/neverdecel/code/vacai/logs/daily_scan_$(date +%Y%m%d).log

# View all daily logs
ls -lh /home/neverdecel/code/vacai/logs/daily_scan_*.log
```

## Reports

Daily reports are stored in `/home/neverdecel/code/vacai/reports/`:

- `daily_scan_YYYYMMDD.md` - Daily incremental reports
- `job_scan_report.md` - Comprehensive report (generated on demand)

## Notifications (Optional)

To receive notifications for new strong matches, you can:

### Option 1: Email Notifications

Create `scripts/notify_new_matches.py`:

```python
from src.database.manager import DatabaseManager
import smtplib
from email.message import EmailMessage

db = DatabaseManager()
new_strong = db.get_new_strong_matches(hours=24, min_score=80)

if new_strong:
    msg = EmailMessage()
    msg['Subject'] = f'VACAI: {len(new_strong)} New Strong Job Match(es)!'
    msg['From'] = 'your-email@gmail.com'
    msg['To'] = 'your-email@gmail.com'

    body = f"You have {len(new_strong)} new strong match(es):\\n\\n"
    for job in new_strong:
        body += f"- {job.title} at {job.company} ({job.overall_score}/100)\\n"

    msg.set_content(body)

    # Send email (configure SMTP settings)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your-email@gmail.com', 'your-app-password')
        smtp.send_message(msg)
```

Then uncomment the notification section in `daily_scan.sh` (lines 60-63).

### Option 2: Desktop Notifications

Add to `daily_scan.sh` after report generation:

```bash
# Show desktop notification for strong matches
if [ $strong_count -gt 0 ]; then
    notify-send "VACAI Job Alert" "$strong_count new strong match(es) found!" -u critical
fi
```

## Customization

### Adjust Scan Timing

Change cron schedule:
- `0 9 * * *` = 9:00 AM daily
- `0 6,18 * * *` = 6:00 AM and 6:00 PM daily
- `0 */6 * * *` = Every 6 hours

### Adjust Cleanup Settings

Modify cleanup parameters:
```bash
# More aggressive (remove older jobs with higher threshold)
python main.py cleanup --days 14 --min-score 70

# Less aggressive (keep jobs longer)
python main.py cleanup --days 60 --min-score 50
```

### Filter Search Terms

Edit `config/search_preferences.yml` to adjust:
- Search terms
- Locations
- Keywords to avoid
- Salary expectations
- Work mode preferences

## Monitoring

Check if automation is running correctly:

```bash
# Check cron status
systemctl status cron

# View cron logs
grep CRON /var/log/syslog | tail -20

# Check VACAI stats
cd /home/neverdecel/code/vacai
source venv/bin/activate
python main.py stats
```

## Troubleshooting

### Cron job not running?

1. Check cron service:
```bash
systemctl status cron
```

2. Check permissions:
```bash
ls -la /home/neverdecel/code/vacai/*.sh
# Should show -rwxr-xr-x (executable)
```

3. Check logs:
```bash
grep VACAI /var/log/syslog
```

### Jobs not being scored?

1. Check OpenAI API key:
```bash
cat /home/neverdecel/code/vacai/config/.env | grep OPENAI_API_KEY
```

2. Check unscored jobs:
```bash
python main.py stats
# Look at "Scored jobs" vs "Total jobs"
```

3. Run manual test:
```bash
python main.py daily
```

### Database too large?

Run cleanup more frequently:
```bash
# Clean up jobs older than 14 days
python main.py cleanup --days 14 --min-score 60
```

## Cost Estimation

With GPT-4o-mini scoring (~$0.01-0.02 per 100 jobs):

- **Daily**: 20 new jobs = $0.002-0.004/day = ~$0.10/month
- **Weekly**: 140 new jobs = $0.014-0.028/week = ~$0.10/month
- **Monthly Total**: ~$0.10-0.20/month

Resume analysis (GPT-4o) is one-time cost: ~$0.05-0.10

## Support

For issues or questions:
- Check logs in `/home/neverdecel/code/vacai/logs/`
- Review reports in `/home/neverdecel/code/vacai/reports/`
- Run `python main.py stats` to check system status
