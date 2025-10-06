"""Generate formatted reports of job matches"""

from typing import List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown


console = Console()


def format_salary(min_sal, max_sal, currency="USD"):
    """Format salary range"""
    if min_sal and max_sal:
        return f"${min_sal:,.0f} - ${max_sal:,.0f}"
    elif min_sal:
        return f"${min_sal:,.0f}+"
    elif max_sal:
        return f"Up to ${max_sal:,.0f}"
    else:
        return "Not specified"


def print_job_summary(jobs: List):
    """Print summary table of jobs"""

    if not jobs:
        console.print("📭 No jobs found", style="yellow")
        return

    table = Table(title=f"Top Job Matches ({len(jobs)} jobs)")

    table.add_column("#", style="cyan", width=3)
    table.add_column("Score", justify="right", style="green", width=6)
    table.add_column("Title", style="bold", width=30)
    table.add_column("Company", width=20)
    table.add_column("Location", width=20)
    table.add_column("Salary", width=20)

    for i, job in enumerate(jobs, 1):
        score = job.overall_score or 0
        score_style = "green" if score >= 80 else "yellow" if score >= 60 else "red"

        salary = format_salary(job.min_salary, job.max_salary)

        table.add_row(
            str(i),
            f"{score}/100",
            job.title[:30],
            job.company[:20],
            (job.location or "")[:20],
            salary
        )

    console.print(table)


def print_job_detail(job, rank: int = 1):
    """Print detailed view of a single job"""

    # Header
    score = job.overall_score or 0
    score_style = "green" if score >= 80 else "yellow" if score >= 60 else "red"

    header = f"""# #{rank}: {job.title}

**Company:** {job.company}
**Location:** {job.location or 'Not specified'}
**Salary:** {format_salary(job.min_salary, job.max_salary)}
**Type:** {job.job_type or 'Not specified'}
**Posted:** {job.posted_date.strftime('%Y-%m-%d') if job.posted_date else 'Unknown'}
**Source:** {job.source}
"""

    console.print(Panel(Markdown(header), border_style=score_style))

    # AI Scoring
    if job.ai_score:
        score_data = job.ai_score

        # Overall score
        console.print(f"\n[bold]Overall Score: {score}/100[/bold] ({score_data.get('decision', 'unknown')})\n")

        # Dimension scores
        dimensions = Table(show_header=False, box=None)
        dimensions.add_column("Dimension", style="cyan")
        dimensions.add_column("Score", justify="right")

        dimensions.add_row("Skills Match", f"{score_data.get('skills_match', 0)}/100")
        dimensions.add_row("Experience Fit", f"{score_data.get('experience_fit', 0)}/100")
        dimensions.add_row("Salary Alignment", f"{score_data.get('salary_alignment', 0)}/100")
        dimensions.add_row("Culture Fit", f"{score_data.get('culture_fit', 0)}/100")
        dimensions.add_row("Growth Potential", f"{score_data.get('growth_potential', 0)}/100")
        dimensions.add_row("Commute Feasibility", f"{score_data.get('commute_feasibility', 0)}/100")

        # Highlight employment type with color coding
        employment_score = score_data.get('employment_type_fit', 0)
        employment_style = "green" if employment_score >= 80 else "red"
        dimensions.add_row(
            "Employment Type (In-house)",
            f"[{employment_style}]{employment_score}/100[/{employment_style}]"
        )

        console.print(dimensions)

        # Summary
        console.print(f"\n[bold]Summary:[/bold]\n{score_data.get('summary', 'N/A')}\n")

        # Highlights
        highlights = score_data.get('match_highlights', [])
        if highlights:
            console.print("[bold green]✓ Match Highlights:[/bold green]")
            for highlight in highlights:
                console.print(f"  • {highlight}")
            console.print()

        # Concerns
        concerns = score_data.get('concerns', [])
        if concerns:
            console.print("[bold yellow]⚠ Concerns:[/bold yellow]")
            for concern in concerns:
                console.print(f"  • {concern}")
            console.print()

    # Job URL
    console.print(f"[bold]Apply:[/bold] {job.job_url}\n")
    console.print("─" * 80 + "\n")


def generate_daily_report(db_manager, min_score: int = 70, limit: int = 20):
    """Generate daily report of top jobs"""

    console.print("\n[bold cyan]🚀 VACAI Daily Job Report[/bold cyan]")
    console.print(f"[dim]Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}[/dim]\n")

    # Get top jobs
    top_jobs = db_manager.get_top_jobs(limit=limit, min_score=min_score)

    if not top_jobs:
        console.print(f"📭 No jobs found with score >= {min_score}", style="yellow")
        return

    # Summary table
    print_job_summary(top_jobs)

    # Ask if user wants details
    console.print(f"\n[dim]Use 'vacai show <job_number>' to see details[/dim]")


def show_job_details(db_manager, job_number: int):
    """Show details for a specific job by rank"""

    # Get top jobs
    top_jobs = db_manager.get_top_jobs(limit=100, min_score=0)

    if job_number < 1 or job_number > len(top_jobs):
        console.print(f"❌ Job #{job_number} not found", style="red")
        return

    job = top_jobs[job_number - 1]
    print_job_detail(job, rank=job_number)
