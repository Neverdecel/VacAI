#!/bin/bash
# VACAI Weekly Cleanup Script
# Remove old low-scoring jobs to prevent database bloat

VACAI_DIR="/home/neverdecel/code/vacai"
LOG_DIR="$VACAI_DIR/logs"
LOG_FILE="$LOG_DIR/cleanup_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting VACAI Database Cleanup ==="

cd "$VACAI_DIR" || { log "ERROR: Failed to cd to $VACAI_DIR"; exit 1; }
source venv/bin/activate || { log "ERROR: Failed to activate venv"; exit 1; }

# Run cleanup (remove jobs older than 30 days with score < 60)
log "Cleaning up old jobs..."
python3 -c "
from src.database.manager import DatabaseManager

db = DatabaseManager()
deleted = db.cleanup_old_jobs(days=30, min_score=60)
print(f'✓ Removed {deleted} old low-scoring jobs')
" >> "$LOG_FILE" 2>&1

log "=== Cleanup Complete ==="

# Keep only last 90 days of cleanup logs
find "$LOG_DIR" -name "cleanup_*.log" -type f -mtime +90 -delete

exit 0
