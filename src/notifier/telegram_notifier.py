"""Telegram notification module for sending daily job reports"""

import os
import asyncio
from typing import List, Optional
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from src.database.models import Job


class TelegramNotifier:
    """Send job reports via Telegram"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize Telegram bot

        Args:
            bot_token: Telegram bot token (from @BotFather)
            chat_id: Chat ID to send messages to (from @userinfobot)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID not set in environment")

        self.bot = Bot(token=self.bot_token)

    def _format_salary(self, min_sal, max_sal) -> str:
        """Format salary range"""
        if min_sal and max_sal:
            return f"€{min_sal:,.0f} - €{max_sal:,.0f}"
        elif min_sal:
            return f"€{min_sal:,.0f}+"
        elif max_sal:
            return f"Up to €{max_sal:,.0f}"
        else:
            return "Not specified"

    def _format_job_message(self, job: Job, rank: int) -> tuple[str, InlineKeyboardMarkup]:
        """Format a single job as a Telegram message with inline button

        Returns:
            Tuple of (message_text, inline_keyboard)
        """
        score = job.overall_score or 0
        score_emoji = "🎯" if score >= 80 else "🟡" if score >= 60 else "🔴"

        salary = self._format_salary(job.min_salary, job.max_salary)

        # Build message
        message = f"{score_emoji} <b>#{rank}: {job.title}</b>\n"
        message += f"<b>{score}/100</b> | {job.company}\n\n"
        message += f"📍 {job.location or 'Not specified'}\n"
        message += f"💰 {salary}\n"

        if job.posted_date:
            message += f"📅 {job.posted_date.strftime('%Y-%m-%d')}\n"

        # Add top highlights if available
        if job.ai_score:
            score_data = job.ai_score

            # Show key dimension scores
            message += f"\n<b>Key Scores:</b>\n"
            message += f"• Skills: {score_data.get('skills_match', 0)}/100\n"
            message += f"• Experience: {score_data.get('experience_fit', 0)}/100\n"
            message += f"• In-house fit: {score_data.get('employment_type_fit', 0)}/100\n"

            # Show top 2 highlights
            highlights = score_data.get('match_highlights', [])
            if highlights:
                message += f"\n<b>✅ Highlights:</b>\n"
                for highlight in highlights[:2]:
                    message += f"• {highlight}\n"

            # Show summary (truncated)
            summary = score_data.get('summary', '')
            if summary:
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                message += f"\n<i>{summary}</i>\n"

        # Create inline button for applying
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Apply Now", url=job.job_url)]
        ])

        return message, keyboard

    async def _send_message(self, text: str, reply_markup=None, parse_mode=ParseMode.HTML):
        """Send a single message"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    async def send_daily_report(self,
                               strong_matches: List[Job],
                               potential_matches: List[Job],
                               new_jobs_count: int = 0):
        """Send daily report via Telegram

        Args:
            strong_matches: Jobs with score >= 80
            potential_matches: Jobs with score 60-79
            new_jobs_count: Total new jobs found today
        """
        today = datetime.now()

        # Send header
        header = f"<b>📊 VACAI Daily Job Report</b>\n"
        header += f"<i>{today.strftime('%A, %B %d, %Y')}</i>\n\n"
        header += f"<b>New Jobs Found:</b> {new_jobs_count}\n"
        header += f"🎯 Strong Matches: {len(strong_matches)}\n"
        header += f"🟡 Potential Matches: {len(potential_matches)}\n"
        header += "─────────────────────"

        await self._send_message(header)

        # Send strong matches
        if strong_matches:
            await self._send_message("<b>🎯 STRONG MATCHES - Apply ASAP!</b>")

            for i, job in enumerate(strong_matches[:10], 1):  # Limit to 10
                message, keyboard = self._format_job_message(job, i)
                await self._send_message(message, reply_markup=keyboard)
                await asyncio.sleep(0.5)  # Avoid rate limiting
        else:
            await self._send_message("<i>No strong matches found today</i>")

        # Send potential matches (collapsed)
        if potential_matches:
            summary = f"\n<b>🟡 Potential Matches ({len(potential_matches)})</b>\n\n"
            for i, job in enumerate(potential_matches[:5], 1):  # Show top 5
                score = job.overall_score or 0
                summary += f"{i}. {job.title} - {job.company} ({score}/100)\n"

            if len(potential_matches) > 5:
                summary += f"\n<i>...and {len(potential_matches) - 5} more</i>"

            await self._send_message(summary)

        # Send footer with next actions
        if strong_matches:
            footer = "\n<b>🔔 Next Actions:</b>\n"
            footer += f"1️⃣ Review {len(strong_matches)} strong match(es)\n"
            footer += "2️⃣ Apply within 24-48 hours\n"
            footer += "3️⃣ Update application tracking\n\n"
        else:
            footer = "\n<i>No urgent action needed today</i>\n\n"

        footer += f"<i>Next scan: Tomorrow at 09:00</i>"

        await self._send_message(footer)

    async def send_test_message(self):
        """Send a test message to verify configuration"""
        test_msg = "✅ <b>VACAI Telegram Bot Connected!</b>\n\n"
        test_msg += "You will receive daily job reports here.\n"
        test_msg += f"<i>Test sent at {datetime.now().strftime('%H:%M:%S')}</i>"

        await self._send_message(test_msg)

    async def send_strong_match_alert(self, job: Job):
        """Send immediate alert for a new strong match

        Args:
            job: Job object with score >= 80
        """
        alert = "🚨 <b>NEW STRONG MATCH ALERT!</b> 🚨\n\n"
        await self._send_message(alert)

        message, keyboard = self._format_job_message(job, rank=1)
        await self._send_message(message, reply_markup=keyboard)


def send_daily_report_sync(strong_matches: List[Job],
                           potential_matches: List[Job],
                           new_jobs_count: int = 0):
    """Synchronous wrapper for sending daily report

    Args:
        strong_matches: Jobs with score >= 80
        potential_matches: Jobs with score 60-79
        new_jobs_count: Total new jobs found today
    """
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_daily_report(strong_matches, potential_matches, new_jobs_count))


def send_test_message_sync():
    """Synchronous wrapper for sending test message"""
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_test_message())


def send_strong_match_alert_sync(job: Job):
    """Synchronous wrapper for sending strong match alert

    Args:
        job: Job object with score >= 80
    """
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_strong_match_alert(job))
