#!/bin/bash
# VACAI Daily Job Scan Automation
# Run this script daily via cron to automatically scan for new jobs

# Configuration
VACAI_DIR="/home/neverdecel/code/vacai"
LOG_DIR="$VACAI_DIR/logs"
LOG_FILE="$LOG_DIR/daily_scan_$(date +%Y%m%d).log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting VACAI Daily Scan ==="

# Change to VACAI directory
cd "$VACAI_DIR" || { log "ERROR: Failed to cd to $VACAI_DIR"; exit 1; }

# Activate virtual environment
source venv/bin/activate || { log "ERROR: Failed to activate venv"; exit 1; }

# Run job scan (only new jobs will be scraped and scored)
log "Running job scan..."
python3 main.py scan >> "$LOG_FILE" 2>&1
SCAN_EXIT_CODE=$?

if [ $SCAN_EXIT_CODE -ne 0 ]; then
    log "WARNING: Scan completed with errors (exit code: $SCAN_EXIT_CODE)"
else
    log "✓ Scan completed successfully"
fi

# Generate daily report
log "Generating daily report..."
python3 -c "
from src.database.manager import DatabaseManager
from src.cli.report_generator import generate_daily_report

db = DatabaseManager()
output_file, strong_count, potential_count = generate_daily_report(db)
print(f'✓ Daily report generated: {output_file}')
print(f'  - Strong matches: {strong_count}')
print(f'  - Potential matches: {potential_count}')
" >> "$LOG_FILE" 2>&1

REPORT_EXIT_CODE=$?

if [ $REPORT_EXIT_CODE -ne 0 ]; then
    log "ERROR: Report generation failed (exit code: $REPORT_EXIT_CODE)"
else
    log "✓ Daily report generated successfully"
fi

# Send Telegram notification
log "Sending Telegram notification..."
python3 -c "
import os
from src.database.manager import DatabaseManager
from src.notifier.telegram_notifier import send_daily_report_sync

# Check if Telegram is configured
if os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'):
    db = DatabaseManager()

    # Get new jobs from last 24 hours
    new_jobs = db.get_jobs_last_24h()
    strong_matches = [j for j in new_jobs if j.overall_score and j.overall_score >= 80]
    potential_matches = [j for j in new_jobs if j.overall_score and 60 <= j.overall_score < 80]

    send_daily_report_sync(strong_matches, potential_matches, len(new_jobs))
    print(f'✓ Telegram report sent')
    print(f'  - Strong: {len(strong_matches)}, Potential: {len(potential_matches)}')
else:
    print('⚠ Telegram not configured (skipping notification)')
    print('  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to enable')
" >> "$LOG_FILE" 2>&1

TELEGRAM_EXIT_CODE=$?

if [ $TELEGRAM_EXIT_CODE -ne 0 ]; then
    log "WARNING: Telegram notification failed (exit code: $TELEGRAM_EXIT_CODE)"
else
    log "✓ Telegram notification sent successfully"
fi

# Show summary
log "=== Daily Scan Complete ==="
log "Log file: $LOG_FILE"
log "Reports directory: $VACAI_DIR/reports"

# Keep only last 30 days of logs
find "$LOG_DIR" -name "daily_scan_*.log" -type f -mtime +30 -delete

exit 0
