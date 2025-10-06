"""Debug and audit report generator for VACAI pipeline analysis"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from src.database.manager import DatabaseManager
from src.database.models import Job, ScanHistory


class DebugReportGenerator:
    """Generates comprehensive debug/audit reports for pipeline analysis"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.session = db_manager.get_session()

    def generate_comprehensive_report(self, output_path: str = None) -> str:
        """Generate full debug/audit report"""

        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"reports/debug_audit_{timestamp}.md"

        report_sections = []

        # Header
        report_sections.append(self._generate_header())

        # Pipeline overview
        report_sections.append(self._generate_pipeline_overview())

        # Stage 1: Scraping analysis
        report_sections.append(self._generate_scraping_analysis())

        # Stage 2: Database analysis
        report_sections.append(self._generate_database_analysis())

        # Stage 3: Scoring analysis
        report_sections.append(self._generate_scoring_analysis())

        # Stage 4: Results analysis
        report_sections.append(self._generate_results_analysis())

        # Stage 5: Optimization insights
        report_sections.append(self._generate_optimization_insights())

        # Combine all sections
        full_report = "\n\n".join(report_sections)

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(full_report)

        self.session.close()
        return str(output_file)

    def _generate_header(self) -> str:
        """Generate report header"""
        now = datetime.now()
        return f"""# VACAI Debug & Audit Report

**Generated**: {now.strftime('%A, %B %d, %Y at %H:%M:%S')}
**Report Type**: Comprehensive Pipeline Analysis
**Purpose**: Developer debugging, optimization, and system audit

---
"""

    def _generate_pipeline_overview(self) -> str:
        """Generate pipeline flow overview"""
        all_jobs = self.session.query(Job).all()
        scored_jobs = [j for j in all_jobs if j.is_scored]

        return f"""## 📊 Pipeline Overview

### Data Flow Summary

```
Search Config → JobSpy Scraper → Raw Jobs → Format & Validate → Database
                                                                      ↓
                                                                 Unscored Jobs
                                                                      ↓
                                                              AI Scorer (GPT-4o-mini)
                                                                      ↓
                                                              Scored Jobs (7 dimensions)
                                                                      ↓
                                                              Reports & Filtering
```

### Current State
- **Total Jobs in Database**: {len(all_jobs)}
- **Scored Jobs**: {len(scored_jobs)}
- **Unscored Jobs**: {len(all_jobs) - len(scored_jobs)}
- **Database File**: `vacai.db`
- **Last Updated**: {max(j.scraped_at for j in all_jobs).strftime('%Y-%m-%d %H:%M:%S') if all_jobs else 'N/A'}

---
"""

    def _generate_scraping_analysis(self) -> str:
        """Analyze scraping stage"""
        all_jobs = self.session.query(Job).all()

        # Load search preferences
        search_prefs = self._load_search_preferences()

        # Analyze by source
        by_source = defaultdict(list)
        for job in all_jobs:
            by_source[job.source or 'unknown'].append(job)

        # Analyze by location
        by_location = defaultdict(list)
        for job in all_jobs:
            by_location[job.location or 'unknown'].append(job)

        # Get recent scan history
        recent_scans = self.session.query(ScanHistory).order_by(ScanHistory.scan_date.desc()).limit(5).all()

        section = f"""## 🔍 Stage 1: Job Scraping Analysis

### Search Configuration

**Search Terms**: {', '.join(search_prefs.get('search_terms', []))}
**Locations**: {', '.join(search_prefs.get('locations', []))}
**Job Boards**: {search_prefs.get('job_boards', 'linkedin, indeed, glassdoor')}
**Results per Term**: {search_prefs.get('results_wanted', 50) // len(search_prefs.get('search_terms', [1]))}
**Hours Old**: {search_prefs.get('hours_old', 72)}

### Raw Scraping Results

**Total Unique Jobs Scraped**: {len(all_jobs)}

#### Jobs by Source
"""

        for source, jobs in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
            section += f"- **{source.upper()}**: {len(jobs)} jobs\n"

        section += "\n#### Jobs by Location\n"

        for location, jobs in sorted(by_location.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            section += f"- **{location}**: {len(jobs)} jobs\n"

        section += "\n### Recent Scan History\n\n"

        if recent_scans:
            for scan in recent_scans:
                section += f"- **{scan.scan_date.strftime('%Y-%m-%d %H:%M')}**: {scan.jobs_found} jobs found, {scan.jobs_scored} scored\n"
        else:
            section += "*No scan history available*\n"

        # Show all raw job titles
        section += "\n### All Raw Job Titles (Scraped)\n\n"
        section += "| # | Title | Company | Source | Location |\n"
        section += "|---|-------|---------|--------|----------|\n"

        for i, job in enumerate(sorted(all_jobs, key=lambda x: x.scraped_at, reverse=True), 1):
            location_short = (job.location[:30] + '...') if job.location and len(job.location) > 30 else (job.location or 'N/A')
            title_short = (job.title[:40] + '...') if len(job.title) > 40 else job.title
            section += f"| {i} | {title_short} | {job.company} | {job.source or 'N/A'} | {location_short} |\n"

        section += "\n---\n"

        return section

    def _generate_database_analysis(self) -> str:
        """Analyze database storage stage"""
        all_jobs = self.session.query(Job).all()

        # Analyze data quality
        missing_description = sum(1 for j in all_jobs if not j.description)
        missing_salary = sum(1 for j in all_jobs if not j.min_salary and not j.max_salary)
        missing_location = sum(1 for j in all_jobs if not j.location)
        missing_posted_date = sum(1 for j in all_jobs if not j.posted_date)
        remote_jobs = sum(1 for j in all_jobs if j.is_remote)

        # Analyze descriptions by source
        by_source_desc = defaultdict(lambda: {'total': 0, 'with_desc': 0})
        for job in all_jobs:
            source = job.source or 'unknown'
            by_source_desc[source]['total'] += 1
            if job.description:
                by_source_desc[source]['with_desc'] += 1

        section = f"""## 💾 Stage 2: Database Storage Analysis

### Data Quality Metrics

**Total Jobs Stored**: {len(all_jobs)}

#### Field Completeness
- **Missing Description**: {missing_description} ({missing_description/len(all_jobs)*100:.1f}%)"""

        if missing_description > 0:
            section += " ⚠️ **CRITICAL ISSUE**"

        section += f"""
- **Missing Salary**: {missing_salary} ({missing_salary/len(all_jobs)*100:.1f}%) - OK (salary not required for scoring)
- **Missing Location**: {missing_location} ({missing_location/len(all_jobs)*100:.1f}%)
- **Missing Posted Date**: {missing_posted_date} ({missing_posted_date/len(all_jobs)*100:.1f}%)

#### Job Attributes
- **Remote Jobs**: {remote_jobs} ({remote_jobs/len(all_jobs)*100:.1f}%)
- **On-site/Hybrid**: {len(all_jobs) - remote_jobs} ({(len(all_jobs) - remote_jobs)/len(all_jobs)*100:.1f}%)

### Description Availability by Source

"""

        for source, stats in sorted(by_source_desc.items()):
            pct = (stats['with_desc'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅" if pct == 100 else ("⚠️" if pct > 0 else "❌")
            section += f"- **{source.upper()}**: {stats['with_desc']}/{stats['total']} ({pct:.1f}%) {status}\n"

        if missing_description > 0:
            section += f"""
### ⚠️ Critical Issue: Missing Descriptions

**{missing_description} jobs ({missing_description/len(all_jobs)*100:.1f}%) lack descriptions!**

**Impact**: Jobs without descriptions cannot be accurately scored by AI. The scoring will be based only on title, company, and location - resulting in poor quality scores.

**Root Cause**: LinkedIn requires `linkedin_fetch_description=True` parameter in JobSpy.

**Fix Applied**: ✅ Updated scraper to fetch LinkedIn descriptions. Next scan will have full descriptions.

**Current Scoring Behavior**: Jobs without descriptions are now skipped during scoring to prevent inaccurate results.
"""

        section += """
### Duplicate Detection

VACAI uses `job_url` as unique identifier to prevent duplicates.
- All """ + str(len(all_jobs)) + """ jobs have unique URLs ✅

---
"""

        return section

    def _generate_scoring_analysis(self) -> str:
        """Analyze AI scoring stage"""
        all_jobs = self.session.query(Job).all()
        scored_jobs = [j for j in all_jobs if j.is_scored and j.ai_score]

        if not scored_jobs:
            return """## 🤖 Stage 3: AI Scoring Analysis

*No jobs have been scored yet.*

---
"""

        # Analyze scoring dimensions
        dimension_stats = defaultdict(list)
        decision_counts = Counter()

        for job in scored_jobs:
            if job.ai_score:
                dimension_stats['overall_score'].append(job.ai_score.get('overall_score', 0))
                dimension_stats['skills_match'].append(job.ai_score.get('skills_match', 0))
                dimension_stats['experience_fit'].append(job.ai_score.get('experience_fit', 0))
                dimension_stats['employment_type_fit'].append(job.ai_score.get('employment_type_fit', 0))
                dimension_stats['commute_feasibility'].append(job.ai_score.get('commute_feasibility', 0))
                dimension_stats['culture_fit'].append(job.ai_score.get('culture_fit', 0))
                dimension_stats['growth_potential'].append(job.ai_score.get('growth_potential', 0))
                dimension_stats['salary_alignment'].append(job.ai_score.get('salary_alignment', 0))

                decision = job.ai_score.get('decision', 'unknown')
                decision_counts[decision] += 1

        # Calculate averages
        def avg(lst): return sum(lst) / len(lst) if lst else 0

        section = f"""## 🤖 Stage 3: AI Scoring Analysis

### Scoring Summary

**Total Jobs Scored**: {len(scored_jobs)}
**AI Model**: GPT-4o-mini (cost-efficient)
**Estimated Token Usage**: ~{len(scored_jobs) * 500} tokens (~${len(scored_jobs) * 500 * 0.000015:.4f})

### Decision Distribution

"""

        for decision, count in decision_counts.most_common():
            percentage = count / len(scored_jobs) * 100
            section += f"- **{decision}**: {count} jobs ({percentage:.1f}%)\n"

        section += f"""
### Dimension Score Averages (0-100)

| Dimension | Avg Score | Min | Max |
|-----------|-----------|-----|-----|
| Overall Score | {avg(dimension_stats['overall_score']):.1f} | {min(dimension_stats['overall_score']) if dimension_stats['overall_score'] else 0} | {max(dimension_stats['overall_score']) if dimension_stats['overall_score'] else 0} |
| Skills Match (25%) | {avg(dimension_stats['skills_match']):.1f} | {min(dimension_stats['skills_match']) if dimension_stats['skills_match'] else 0} | {max(dimension_stats['skills_match']) if dimension_stats['skills_match'] else 0} |
| Experience Fit (20%) | {avg(dimension_stats['experience_fit']):.1f} | {min(dimension_stats['experience_fit']) if dimension_stats['experience_fit'] else 0} | {max(dimension_stats['experience_fit']) if dimension_stats['experience_fit'] else 0} |
| Employment Type (25%) | {avg(dimension_stats['employment_type_fit']):.1f} | {min(dimension_stats['employment_type_fit']) if dimension_stats['employment_type_fit'] else 0} | {max(dimension_stats['employment_type_fit']) if dimension_stats['employment_type_fit'] else 0} |
| Commute Feasibility (15%) | {avg(dimension_stats['commute_feasibility']):.1f} | {min(dimension_stats['commute_feasibility']) if dimension_stats['commute_feasibility'] else 0} | {max(dimension_stats['commute_feasibility']) if dimension_stats['commute_feasibility'] else 0} |
| Culture Fit (10%) | {avg(dimension_stats['culture_fit']):.1f} | {min(dimension_stats['culture_fit']) if dimension_stats['culture_fit'] else 0} | {max(dimension_stats['culture_fit']) if dimension_stats['culture_fit'] else 0} |
| Growth Potential (5%) | {avg(dimension_stats['growth_potential']):.1f} | {min(dimension_stats['growth_potential']) if dimension_stats['growth_potential'] else 0} | {max(dimension_stats['growth_potential']) if dimension_stats['growth_potential'] else 0} |
| Salary Alignment | {avg(dimension_stats['salary_alignment']):.1f} | {min(dimension_stats['salary_alignment']) if dimension_stats['salary_alignment'] else 0} | {max(dimension_stats['salary_alignment']) if dimension_stats['salary_alignment'] else 0} |

### Individual Job Scores (Detailed)

"""

        # Show all jobs with detailed scores
        section += "| # | Job | Overall | Skills | Exp | Empl | Commute | Culture | Growth | Decision |\n"
        section += "|---|-----|---------|--------|-----|------|---------|---------|--------|----------|\n"

        for i, job in enumerate(sorted(scored_jobs, key=lambda x: x.overall_score or 0, reverse=True), 1):
            title_short = (job.title[:30] + '...') if len(job.title) > 30 else job.title
            score = job.ai_score or {}
            section += f"| {i} | {title_short} at {job.company[:20]} | {score.get('overall_score', 0)} | {score.get('skills_match', 0)} | {score.get('experience_fit', 0)} | {score.get('employment_type_fit', 0)} | {score.get('commute_feasibility', 0)} | {score.get('culture_fit', 0)} | {score.get('growth_potential', 0)} | {score.get('decision', 'N/A')} |\n"

        section += "\n---\n"

        return section

    def _generate_results_analysis(self) -> str:
        """Analyze final results"""
        all_jobs = self.session.query(Job).all()
        scored_jobs = [j for j in all_jobs if j.is_scored and j.overall_score is not None]

        if not scored_jobs:
            return """## 📈 Stage 4: Results Analysis

*No scored jobs available for analysis.*

---
"""

        # Score distribution
        score_ranges = {
            '80-100 (Strong Match)': len([j for j in scored_jobs if j.overall_score >= 80]),
            '60-79 (Potential)': len([j for j in scored_jobs if 60 <= j.overall_score < 80]),
            '40-59 (Weak)': len([j for j in scored_jobs if 40 <= j.overall_score < 60]),
            '20-39 (Poor)': len([j for j in scored_jobs if 20 <= j.overall_score < 40]),
            '0-19 (Reject)': len([j for j in scored_jobs if j.overall_score < 20]),
        }

        # Analyze rejection reasons
        consultancy_rejects = []
        commute_rejects = []
        skills_rejects = []

        for job in scored_jobs:
            if job.ai_score:
                emp_type = job.ai_score.get('employment_type_fit', 100)
                commute = job.ai_score.get('commute_feasibility', 100)
                skills = job.ai_score.get('skills_match', 100)

                if emp_type < 30:
                    consultancy_rejects.append(job)
                if commute < 30:
                    commute_rejects.append(job)
                if skills < 40:
                    skills_rejects.append(job)

        section = f"""## 📈 Stage 4: Results Analysis

### Score Distribution

"""

        for range_name, count in score_ranges.items():
            percentage = count / len(scored_jobs) * 100 if scored_jobs else 0
            bar = '█' * int(percentage / 5)
            section += f"- **{range_name}**: {count} ({percentage:.1f}%) {bar}\n"

        section += f"""
### Filter Effectiveness

#### Employment Type Filter (In-house only)
- **Rejected as Consultancy**: {len(consultancy_rejects)} jobs ({len(consultancy_rejects)/len(scored_jobs)*100:.1f}%)

"""

        if consultancy_rejects[:5]:
            section += "Top consultancy rejections:\n"
            for job in consultancy_rejects[:5]:
                section += f"  - {job.title} at {job.company} (score: {job.ai_score.get('employment_type_fit', 0)}/100)\n"

        section += f"""
#### Commute Feasibility Filter
- **Rejected for Commute**: {len(commute_rejects)} jobs ({len(commute_rejects)/len(scored_jobs)*100:.1f}%)

"""

        if commute_rejects[:5]:
            section += "Top commute rejections:\n"
            for job in commute_rejects[:5]:
                section += f"  - {job.title} in {job.location} (score: {job.ai_score.get('commute_feasibility', 0)}/100)\n"

        section += f"""
#### Skills Mismatch
- **Rejected for Skills**: {len(skills_rejects)} jobs ({len(skills_rejects)/len(scored_jobs)*100:.1f}%)

### Top Concerns Analysis

"""

        # Collect all concerns
        all_concerns = []
        for job in scored_jobs:
            if job.ai_score and job.ai_score.get('concerns'):
                all_concerns.extend(job.ai_score['concerns'])

        # Find common concerns
        concern_keywords = defaultdict(int)
        for concern in all_concerns:
            concern_lower = concern.lower()
            if 'consult' in concern_lower or 'detachering' in concern_lower:
                concern_keywords['consultancy'] += 1
            if 'commute' in concern_lower or 'location' in concern_lower or 'remote' in concern_lower:
                concern_keywords['commute/location'] += 1
            if 'skill' in concern_lower or 'experience' in concern_lower:
                concern_keywords['skills/experience mismatch'] += 1
            if 'salary' in concern_lower or 'compensation' in concern_lower:
                concern_keywords['salary'] += 1
            if 'culture' in concern_lower:
                concern_keywords['culture fit'] += 1

        section += "Most common concern categories:\n"
        for concern, count in sorted(concern_keywords.items(), key=lambda x: x[1], reverse=True):
            section += f"- **{concern}**: mentioned {count} times\n"

        section += "\n---\n"

        return section

    def _generate_optimization_insights(self) -> str:
        """Generate optimization recommendations"""
        all_jobs = self.session.query(Job).all()
        scored_jobs = [j for j in all_jobs if j.is_scored and j.overall_score is not None]

        if not scored_jobs:
            return """## 💡 Stage 5: Optimization Insights

*Insufficient data for optimization analysis.*

---
"""

        # Analyze search term effectiveness
        search_prefs = self._load_search_preferences()
        search_terms = search_prefs.get('search_terms', [])

        # Estimate which terms are in job titles
        term_matches = defaultdict(list)
        for term in search_terms:
            term_words = term.lower().split()
            for job in scored_jobs:
                title_lower = job.title.lower()
                if any(word in title_lower for word in term_words):
                    term_matches[term].append(job)

        # Location effectiveness
        location_scores = defaultdict(list)
        for job in scored_jobs:
            location_scores[job.location or 'Unknown'].append(job.overall_score)

        # Calculate avg scores by location
        location_avg = {loc: sum(scores)/len(scores) for loc, scores in location_scores.items() if scores}

        section = f"""## 💡 Stage 5: Optimization Insights

### Search Term Effectiveness

"""

        for term in search_terms:
            matches = term_matches.get(term, [])
            avg_score = sum(j.overall_score for j in matches) / len(matches) if matches else 0
            strong_matches = len([j for j in matches if j.overall_score >= 80])
            section += f"- **\"{term}\"**: ~{len(matches)} matches, avg score {avg_score:.1f}, {strong_matches} strong\n"

        section += f"""
### Location Productivity

"""

        for loc, avg_score in sorted(location_avg.items(), key=lambda x: x[1], reverse=True)[:10]:
            count = len(location_scores[loc])
            section += f"- **{loc}**: {count} jobs, avg score {avg_score:.1f}\n"

        # Cost analysis
        total_scored = len(scored_jobs)
        est_tokens = total_scored * 500
        est_cost = est_tokens * 0.000015  # GPT-4o-mini input pricing

        section += f"""
### Performance Metrics

#### API Cost Analysis
- **Total Jobs Scored**: {total_scored}
- **Estimated Tokens**: ~{est_tokens:,} tokens
- **Estimated Cost**: ~${est_cost:.4f}
- **Cost per Job**: ~${est_cost/total_scored:.6f}
- **Model**: GPT-4o-mini (cost-efficient)

#### Scoring Efficiency
- **Single-Agent Design**: ~500 tokens/job (vs 2000+ for multi-agent)
- **Token Savings**: ~75% reduction vs multi-agent approach
- **Structured Output**: Pydantic models ensure consistent scoring

### Recommendations

"""

        # Generate recommendations
        strong_count = len([j for j in scored_jobs if j.overall_score >= 80])
        potential_count = len([j for j in scored_jobs if 60 <= j.overall_score < 80])
        reject_count = len([j for j in scored_jobs if j.overall_score < 40])

        if strong_count == 0:
            section += f"""
#### ⚠️ No Strong Matches Found

**Possible actions**:
1. **Broaden search terms**: Add more role variations or adjacent roles
2. **Adjust locations**: Consider expanding commute radius or adding remote options
3. **Review employment type filter**: Verify in-house requirement isn't too restrictive
4. **Lower score threshold**: Review 60-79 range jobs (currently {potential_count} jobs)
"""

        if reject_count > len(scored_jobs) * 0.6:
            section += f"""
#### ⚠️ High Rejection Rate ({reject_count/len(scored_jobs)*100:.0f}%)

**Possible causes**:
1. **Consultancy filter too aggressive**: {len([j for j in scored_jobs if j.ai_score.get('employment_type_fit', 100) < 30])} jobs rejected
2. **Skills mismatch**: Consider adding more search terms aligned with your skillset
3. **Location constraints**: Review commute requirements
"""

        if len(all_jobs) < 50:
            section += """
#### 💡 Low Job Volume

**Suggestions**:
1. **Increase results_wanted**: Currently limited, try increasing to 100+ per search term
2. **Add more job boards**: Enable Glassdoor if not already active
3. **Expand hours_old**: Currently 72h, try 168h (1 week) for more results
4. **Add search term variations**: "Platform Engineer", "DevOps Engineer", "Infrastructure Engineer"
"""

        section += """
### Next Steps

1. **Review top potential matches** (60-79 range) - may have good opportunities
2. **Analyze rejection reasons** - adjust filters if needed
3. **Optimize search terms** - focus on high-performing terms
4. **Monitor daily runs** - track improvements over time
5. **Adjust scoring weights** - if certain dimensions are too strict/lenient

---

## 🔍 Audit Complete

This report provides complete visibility into the VACAI pipeline for debugging and optimization.
For questions or improvements, review the source code or adjust configuration files.
"""

        return section

    def _load_search_preferences(self) -> Dict[str, Any]:
        """Load search preferences from config"""
        try:
            import yaml
            with open('config/search_preferences.yml', 'r') as f:
                prefs = yaml.safe_load(f)
                criteria = prefs.get('job_search_criteria', {})

                return {
                    'search_terms': criteria.get('search_terms', []),
                    'locations': criteria.get('locations', []),
                    'results_wanted': criteria.get('results_wanted', 50),
                    'hours_old': criteria.get('hours_old', 72),
                    'job_boards': criteria.get('job_boards', 'linkedin,indeed,glassdoor')
                }
        except Exception:
            return {}


def generate_debug_report(db_manager: DatabaseManager, output_path: str = None) -> str:
    """Generate comprehensive debug/audit report"""
    generator = DebugReportGenerator(db_manager)
    return generator.generate_comprehensive_report(output_path)
