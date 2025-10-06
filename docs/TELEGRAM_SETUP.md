# Telegram Integration Setup

VACAI can send daily job reports directly to your Telegram account with clickable links for easy application.

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/start` to BotFather
3. Send `/newbot` to create a new bot
4. Follow the prompts to name your bot (e.g., "VACAI Job Scanner")
5. BotFather will give you a **bot token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. **Save this token** - you'll need it for the `.env` file

### 2. Get Your Chat ID

1. Search for `@userinfobot` on Telegram
2. Send `/start` to the bot
3. The bot will reply with your **chat ID** (a number like `123456789`)
4. **Save this chat ID** - you'll need it for the `.env` file

### 3. Start Your Bot

1. Search for your bot on Telegram (use the username from step 1)
2. Send `/start` to your bot to activate the conversation

### 4. Configure VACAI

1. Copy the environment template:
   ```bash
   cp config/.env.example .env
   ```

2. Edit `.env` and add your Telegram credentials:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

### 5. Test the Connection

Run the test command to verify everything works:

```bash
python main.py test-telegram
```

You should receive a test message in your Telegram chat!

## Usage

### Manual Report Sending

Send a report on demand:

```bash
# Send report of jobs from last 24 hours
python main.py send-report

# Customize time range (last 48 hours)
python main.py send-report --hours 48

# Filter by minimum score
python main.py send-report --min-score 70
```

### Automatic Daily Reports

The `daily_scan.sh` script automatically sends Telegram notifications after each scan.

To set up daily automation:

```bash
# Make the script executable
chmod +x daily_scan.sh

# Add to crontab for daily 9 AM execution
crontab -e

# Add this line:
0 9 * * * /home/your_username/code/vacai/daily_scan.sh
```

See `DAILY_AUTOMATION.md` for more details on cron setup.

## What You'll Receive

### Daily Report Format

Each day you'll receive:

1. **Summary Header**
   - Total new jobs found
   - Count of strong matches (80+)
   - Count of potential matches (60-79)

2. **Strong Matches** (80-100 score)
   - Full job details
   - Key scores (skills, experience, in-house fit)
   - Top 2 match highlights
   - AI summary
   - **"Apply Now" button** with direct link

3. **Potential Matches** (60-79 score)
   - Condensed list with top 5 jobs
   - Title, company, and score

4. **Next Actions**
   - Recommended steps based on matches found

### Message Features

- 🎯 **Strong match indicator** for priority jobs
- 🟡 **Potential match indicator** for good fits
- **Inline "Apply Now" buttons** - click to open job posting
- **Rich formatting** - bold, italic, organized sections
- **Condensed format** - key info without overwhelming detail

## Troubleshooting

### "TELEGRAM_BOT_TOKEN not set"
- Make sure you've created `.env` from `.env.example`
- Check that the token is correctly pasted (no extra spaces)
- Ensure `.env` is in the root directory of the project

### "Failed to send message"
- Verify you've sent `/start` to your bot
- Check that chat ID is correct (numbers only, no spaces)
- Try the test command: `python main.py test-telegram`

### "Telegram not configured (skipping notification)"
- This is normal if you haven't set up Telegram yet
- The daily scan will still work, just without notifications
- Follow the setup steps above to enable

### Rate Limiting
- Telegram has rate limits (30 messages/second)
- VACAI includes delays between messages to avoid this
- If you hit limits, try reducing the number of jobs sent

## Privacy & Security

- Your bot token is like a password - keep it secret
- Only share it in the `.env` file (which should NOT be committed to git)
- The `.gitignore` is already configured to exclude `.env`
- Your chat ID is not sensitive but is unique to you

## Advanced Usage

### Customizing Message Format

Edit `src/notifier/telegram_notifier.py` to customize:
- Message text and emojis
- Number of jobs sent
- Highlight criteria
- Button text and formatting

### Sending Immediate Alerts

For new strong matches (>80 score), you can enable immediate alerts by uncommenting the relevant section in your scoring logic.

## Support

If you encounter issues:
1. Test with `python main.py test-telegram`
2. Check logs in `logs/daily_scan_*.log`
3. Verify Telegram credentials in `.env`
4. Ensure `python-telegram-bot` is installed: `pip install -r requirements.txt`
