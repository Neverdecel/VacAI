# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in VacAI, please email the maintainers or create a private security advisory on GitHub.

**Please do not create public issues for security vulnerabilities.**

### What to include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Security Best Practices

### API Keys
- Never commit API keys to the repository
- Use environment variables via `.env` file
- Add `.env` to `.gitignore`
- Rotate keys if accidentally exposed

### Database
- Database files (`.db`, `.sqlite`) are gitignored by default
- Contains potentially personal job search data
- Backup regularly, store securely

### Docker
- Images run as non-root user
- Use secrets management for production deployments
- Keep base images updated

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| < 1.0   | :x:                |
