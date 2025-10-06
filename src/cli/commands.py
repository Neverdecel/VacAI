"""CLI commands for VACAI"""

import os
import click
from pathlib import Path
from dotenv import load_dotenv

from src.agents.resume_analyzer import analyze_resume_file
from src.agents.job_scorer import batch_score_jobs
from src.scraper.job_scraper import scrape_and_save
from src.database.manager import DatabaseManager
from src.cli.report_generator import generate_markdown_report, generate_daily_report as generate_daily_md_report
from src.cli.report import generate_daily_report, show_job_details
from src.cli.debug_report import generate_debug_report
from src.notifier.telegram_notifier import send_daily_report_sync, send_test_message_sync


# Load environment variables
load_dotenv()


@click.group()
def cli():
    """VACAI - AI-Powered Job Search Automation"""
    pass


@cli.command()
@click.option('--resume', '-r', required=True, type=click.Path(exists=True), help='Path to resume file (.txt, .md)')
def init(resume):
    """Initialize VACAI by analyzing your resume"""

    click.echo("🤖 Analyzing your resume with AI...")

    try:
        preferences = analyze_resume_file(resume)

        click.echo("\n✅ Setup complete! Your search preferences have been generated.")
        click.echo("\nNext steps:")
        click.echo("  1. Review config/search_preferences.yml")
        click.echo("  2. Run 'vacai scan' to start finding jobs")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--max-jobs', '-n', type=int, help='Maximum number of jobs to scrape')
def scan(max_jobs):
    """Scrape jobs and score them with AI"""

    db = DatabaseManager()

    # Step 1: Scrape jobs
    click.echo("🔍 Scraping job postings...")
    try:
        jobs_found = scrape_and_save(db)

        if jobs_found == 0:
            click.echo("❌ No jobs found. Try adjusting your search preferences.")
            return

    except Exception as e:
        click.echo(f"❌ Error scraping jobs: {str(e)}", err=True)
        raise click.Abort()

    # Step 2: Score jobs
    click.echo("\n🤖 Scoring jobs with AI...")
    try:
        jobs_scored = batch_score_jobs(db, max_jobs=max_jobs)

        click.echo(f"\n✅ Scan complete!")
        click.echo(f"   Jobs found: {jobs_found}")
        click.echo(f"   Jobs scored: {jobs_scored}")
        click.echo("\nRun 'vacai report' to see top matches")

    except Exception as e:
        click.echo(f"❌ Error scoring jobs: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--min-score', '-s', type=int, default=70, help='Minimum score threshold')
@click.option('--limit', '-l', type=int, default=20, help='Maximum jobs to show')
def report(min_score, limit):
    """Generate report of top job matches"""

    db = DatabaseManager()
    generate_daily_report(db, min_score=min_score, limit=limit)


@cli.command()
@click.argument('job_number', type=int)
def show(job_number):
    """Show detailed view of a specific job by rank"""

    db = DatabaseManager()
    show_job_details(db, job_number)


@cli.command()
def stats():
    """Show database statistics"""

    db = DatabaseManager()
    session = db.get_session()

    try:
        from src.database.models import Job, ScanHistory

        total_jobs = session.query(Job).count()
        scored_jobs = session.query(Job).filter_by(is_scored=True).count()
        strong_matches = session.query(Job).filter(Job.overall_score >= 80).count()
        potential_matches = session.query(Job).filter(Job.overall_score >= 60, Job.overall_score < 80).count()

        click.echo("\n📊 VACAI Statistics")
        click.echo(f"   Total jobs: {total_jobs}")
        click.echo(f"   Scored jobs: {scored_jobs}")
        click.echo(f"   Strong matches (80+): {strong_matches}")
        click.echo(f"   Potential matches (60-79): {potential_matches}")

        # Recent scans
        recent_scans = session.query(ScanHistory).order_by(ScanHistory.scan_date.desc()).limit(5).all()
        if recent_scans:
            click.echo("\n📅 Recent Scans:")
            for scan in recent_scans:
                click.echo(f"   {scan.scan_date.strftime('%Y-%m-%d %H:%M')}: {scan.jobs_found} jobs found")

    finally:
        session.close()


@cli.command()
@click.option('--max-jobs', '-n', type=int, help='Maximum number of jobs to score')
def daily(max_jobs):
    """Run daily scan (incremental - only new jobs)"""

    from datetime import datetime

    db = DatabaseManager()

    # Step 1: Scrape jobs (will only add new ones)
    click.echo("🔍 Scraping new job postings...")
    try:
        jobs_found = scrape_and_save(db)

        if jobs_found == 0:
            click.echo("✅ No new jobs found today.")
        else:
            click.echo(f"✅ Found {jobs_found} new job(s)")

    except Exception as e:
        click.echo(f"❌ Error scraping jobs: {str(e)}", err=True)
        raise click.Abort()

    # Step 2: Score only unscored jobs
    unscored = db.get_unscored_jobs()

    if len(unscored) == 0:
        click.echo("✅ All jobs already scored")
    else:
        click.echo(f"\n🤖 Scoring {len(unscored)} new job(s) with AI...")
        try:
            jobs_scored = batch_score_jobs(db, max_jobs=max_jobs)
            click.echo(f"✅ Scored {jobs_scored} job(s)")
        except Exception as e:
            click.echo(f"❌ Error scoring jobs: {str(e)}", err=True)
            raise click.Abort()

    # Step 3: Generate daily report
    click.echo("\n📊 Generating daily report...")
    try:
        output_file, strong_count, potential_count = generate_daily_md_report(db)

        click.echo(f"\n✅ Daily scan complete!")
        click.echo(f"   Report: {output_file}")
        click.echo(f"   🎯 Strong matches: {strong_count}")
        click.echo(f"   🟡 Potential matches: {potential_count}")

        if strong_count > 0:
            click.echo(f"\n🔔 You have {strong_count} new strong match(es)! Review them ASAP.")

    except Exception as e:
        click.echo(f"❌ Error generating report: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--days', '-d', default=30, help='Remove jobs older than this many days')
@click.option('--min-score', '-s', default=60, help='Remove jobs with score below this threshold')
def cleanup(days, min_score):
    """Clean up old low-scoring jobs"""

    db = DatabaseManager()

    click.echo(f"🧹 Cleaning up jobs older than {days} days with score < {min_score}...")

    try:
        removed = db.cleanup_old_jobs(days=days, min_score=min_score)

        if removed == 0:
            click.echo("✅ No jobs to remove")
        else:
            click.echo(f"✅ Removed {removed} old low-scoring job(s)")
            click.echo("   (Jobs that were applied to or bookmarked were preserved)")

    except Exception as e:
        click.echo(f"❌ Error during cleanup: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: reports/debug_audit_[timestamp].md)')
def debug(output):
    """Generate comprehensive debug/audit report for pipeline analysis"""

    db = DatabaseManager()

    click.echo("🔍 Analyzing VACAI pipeline...")
    click.echo("   - Scraping results")
    click.echo("   - Database quality")
    click.echo("   - AI scoring metrics")
    click.echo("   - Optimization insights")

    try:
        output_file = generate_debug_report(db, output_path=output)

        click.echo(f"\n✅ Debug report generated!")
        click.echo(f"   📄 Report: {output_file}")
        click.echo(f"\n💡 Use this report to:")
        click.echo(f"   - Debug pipeline issues")
        click.echo(f"   - Optimize search terms")
        click.echo(f"   - Analyze scoring patterns")
        click.echo(f"   - Improve filter effectiveness")

    except Exception as e:
        click.echo(f"❌ Error generating debug report: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--min-score', '-s', type=int, default=60, help='Minimum score to include')
@click.option('--hours', '-h', type=int, default=24, help='Hours to look back for jobs')
def send_report(min_score, hours):
    """Send job report via Telegram"""

    # Check if Telegram is configured
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat:
        click.echo("❌ Telegram not configured!", err=True)
        click.echo("\nTo enable Telegram notifications:")
        click.echo("1. Create a bot via @BotFather on Telegram")
        click.echo("2. Get your chat ID from @userinfobot")
        click.echo("3. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to your .env file")
        raise click.Abort()

    db = DatabaseManager()

    click.echo(f"📱 Preparing Telegram report (last {hours} hours, min score: {min_score})...")

    try:
        # Get jobs from specified time range
        new_jobs = db.get_jobs_by_date_range(hours=hours)
        strong_matches = [j for j in new_jobs if j.overall_score and j.overall_score >= 80]
        potential_matches = [j for j in new_jobs if j.overall_score and min_score <= j.overall_score < 80]

        if not new_jobs:
            click.echo(f"⚠ No jobs found in the last {hours} hours")
            return

        click.echo(f"   Jobs found: {len(new_jobs)}")
        click.echo(f"   🎯 Strong: {len(strong_matches)}")
        click.echo(f"   🟡 Potential: {len(potential_matches)}")
        click.echo("\n📤 Sending to Telegram...")

        send_daily_report_sync(strong_matches, potential_matches, len(new_jobs))

        click.echo("\n✅ Report sent successfully!")
        click.echo("   Check your Telegram for the report")

    except Exception as e:
        click.echo(f"❌ Error sending Telegram report: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
def test_telegram():
    """Test Telegram bot connection"""

    # Check if Telegram is configured
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat:
        click.echo("❌ Telegram not configured!", err=True)
        click.echo("\nTo enable Telegram notifications:")
        click.echo("1. Create a bot via @BotFather on Telegram")
        click.echo("2. Get your chat ID from @userinfobot")
        click.echo("3. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to your .env file")
        raise click.Abort()

    click.echo("🧪 Testing Telegram connection...")

    try:
        send_test_message_sync()
        click.echo("\n✅ Test message sent!")
        click.echo("   Check your Telegram to confirm")

    except Exception as e:
        click.echo(f"❌ Failed to send test message: {str(e)}", err=True)
        click.echo("\nPossible issues:")
        click.echo("- Invalid bot token")
        click.echo("- Invalid chat ID")
        click.echo("- Bot hasn't been started (send /start to your bot)")
        raise click.Abort()


if __name__ == '__main__':
    cli()
