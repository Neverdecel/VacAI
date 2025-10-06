# Release Checklist for Public Repository

This checklist outlines the steps completed and remaining to prepare VacAI for public release.

## ✅ Completed

### Security & Privacy
- [x] Removed `.env` file with exposed API keys
- [x] Deleted personal resume PDF
- [x] Removed personal config files (search_preferences.yml, resume_profile.json)
- [x] Removed database file with personal data
- [x] Updated `.gitignore` to exclude all sensitive files
- [x] Replaced hardcoded "neverdecel" with "Neverdecel" placeholder

### Documentation
- [x] Created MIT LICENSE
- [x] Created CONTRIBUTING.md
- [x] Created SECURITY.md
- [x] Updated README.md for public audience
- [x] Moved documentation to `/docs` folder
- [x] Created `resume/README.md` with instructions
- [x] Updated setup.py with proper metadata

### Configuration
- [x] All Docker/k8s configs use placeholder username
- [x] GitHub Actions workflow uses `${{ github.repository }}`
- [x] Config example files in place

## ⚠️ Before Publishing

### Critical - Check Git History
```bash
# Check if secrets were committed in history
git log --all --full-history -- .env
git log --all --full-history -- "*.db"
git log --all --full-history -- "resume/*.pdf"
```

If secrets are in git history, you MUST clean them:
```bash
# Option 1: Use git-filter-repo (recommended)
pip install git-filter-repo
git filter-repo --invert-paths --path .env --path '*.db' --force

# Option 2: Start fresh (nuclear option)
# Create new orphan branch, commit everything fresh
```

### Repository Settings

1. **Update repository name/description on GitHub**
   - Description: "AI-powered job search automation with OpenAI integration"
   - Topics: `python`, `ai`, `job-search`, `openai`, `automation`, `career`

2. **Make repository public** (if currently private)
   - Settings → General → Danger Zone → Change visibility

3. **Enable features**
   - ✅ Issues
   - ✅ Discussions (optional)
   - ✅ Projects (optional)
   - ✅ Wiki (optional)

4. **Configure GitHub Actions**
   - Ensure GITHUB_TOKEN has package write permissions
   - Check workflow permissions: Settings → Actions → Workflow permissions

5. **Set up GitHub Container Registry**
   - Package will be at `ghcr.io/YOUR_USERNAME/vacai`
   - Make package public: Packages → vacai → Package settings → Change visibility

### Update Placeholders

Search and replace `Neverdecel` with your actual GitHub username in:
- `docker-compose.yml`
- `README.md`
- `docs/DEPLOYMENT.md`
- `setup.py`
- `k8s/*.yaml`
- `k8s/README.md`

```bash
# Quick find command
grep -r "Neverdecel" .
```

### Final Verification

```bash
# 1. Check no secrets in files
grep -r "sk-proj" . --exclude-dir=.git
grep -r "AAG" . --exclude-dir=.git  # Telegram tokens

# 2. Check gitignore is working
git status --ignored

# 3. Build Docker image locally
docker build -t vacai:test .
docker run --rm vacai:test python --version

# 4. Test basic functionality (with dummy API key)
python main.py --help
```

### Create Initial Release

```bash
# Tag first release
git tag -a v0.1.0 -m "Initial public release"
git push origin v0.1.0
```

This will trigger GitHub Actions to build and push Docker image to GHCR.

## 🚀 Post-Release

1. **Monitor first users**
   - Watch for issues
   - Respond to questions quickly
   - Welcome contributors

2. **Add badges to README** (after first release)
   - Build status
   - Downloads/stars
   - Latest release version

3. **Consider adding**
   - Example screenshots
   - Demo video
   - Sample output reports
   - FAQ section

4. **Promote** (optional)
   - Share on Reddit (r/Python, r/cscareerquestions, r/jobs)
   - Dev.to article
   - Hacker News
   - LinkedIn post

## 📝 Notes

- Keep personal fork separate from public repo if you want to continue using it
- Create separate branch for your personal configurations
- Remember to star your own repo to boost visibility
- Set up GitHub Sponsors if you want (optional)
