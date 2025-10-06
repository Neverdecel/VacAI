# VACAI Daily Automation - Quick Start

## Ready for Daily Use! 🚀

VACAI is now configured for automated daily job scanning. Here's everything you need to know:

## Quick Start

### Set Up Cron (One-Time Setup)

```bash
# Make scripts executable
chmod +x ~/code/vacai/daily_scan.sh
chmod +x ~/code/vacai/cleanup.sh

# Add to crontab
crontab -e

# Add these lines:
0 9 * * * /home/neverdecel/code/vacai/daily_scan.sh          # Daily at 9:00 AM
0 3 * * 0 /home/neverdecel/code/vacai/cleanup.sh             # Weekly Sunday 3:00 AM
```

Done! VACAI will now run automatically every day.

## What Happens Daily

```
Every morning at 9:00 AM:
├── 🔍 Scrape new jobs from LinkedIn, Indeed, Glassdoor
├── 🤖 Score only NEW jobs with AI (no duplicates)
├── 📊 Generate daily report in /reports
└── 🔔 Log results to /logs
```

## Manual Commands

```bash
# Run daily scan now
python main.py daily

# Check stats
python main.py stats

# Clean up old jobs
python main.py cleanup --days 30 --min-score 60

# View full report
cat reports/daily_scan_$(date +%Y%m%d).md
```

## Key Features

✅ **Incremental Processing** - Only new jobs are scored (saves API costs)
✅ **Duplicate Prevention** - Same job never added twice (tracked by URL)
✅ **Smart Cleanup** - Removes old low-scoring jobs automatically
✅ **Daily Reports** - Highlights new strong matches (80+)
✅ **Full Logging** - All operations logged to `/logs`

## File Locations

```
/home/neverdecel/code/vacai/
├── reports/
│   └── daily_scan_YYYYMMDD.md      # Daily reports
├── logs/
│   ├── daily_scan_YYYYMMDD.log     # Scan logs (30 days)
│   └── cleanup_YYYYMMDD.log        # Cleanup logs (90 days)
├── daily_scan.sh                    # Daily automation script
└── cleanup.sh                       # Weekly cleanup script
```

## Check Strong Matches

```bash
# View today's report
cat ~/code/vacai/reports/daily_scan_$(date +%Y%m%d).md

# View logs
tail -f ~/code/vacai/logs/daily_scan_$(date +%Y%m%d).log

# Check database stats
cd ~/code/vacai && source venv/bin/activate
python main.py stats
```

## Expected Costs

With GPT-4o-mini scoring:
- **~$0.10-0.20 per month** (assuming 20 new jobs/day)
- **~$0.002-0.004 per day**

## Monitoring

VACAI tracks:
- New jobs found each day
- Strong matches (80+) requiring immediate action
- Potential matches (60-79) worth reviewing
- Total jobs in database

Check status anytime:
```bash
python main.py stats
```

## Customization

Edit `config/search_preferences.yml` to adjust:
- Search terms and locations
- Keywords to avoid
- Work mode preferences (hybrid/remote/on-site)
- Commute requirements
- Salary expectations

## What Gets Filtered Out

❌ Consultancy/detachering roles
❌ Companies without NL/EU presence
❌ Jobs beyond 30min commute from Haarlem
❌ Remote-only US positions
❌ Entry-level positions

## Full Documentation

See `CRON_SETUP.md` for detailed setup instructions and troubleshooting.

---

**You're all set!** VACAI will now scan for jobs every day and notify you of strong matches. 🎯
