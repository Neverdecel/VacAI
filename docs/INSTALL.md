# Installation Guide

The system is externally managed and requires virtual environment or system packages.

## Option 1: Using System Packages (Recommended)

```bash
# Install Python packages from apt
sudo apt update
sudo apt install python3-full python3-pip python3-venv

# Create virtual environment
cd /home/neverdecel/code/vacai
python3 -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt
```

## Option 2: Using pipx

```bash
sudo apt install pipx
pipx install openai
# ... install other packages
```

## Option 3: Manual Installation

Install each package individually:

```bash
sudo apt install python3-pip
pip3 install --user openai PyPDF2 pydantic pyyaml sqlalchemy python-dotenv click rich python-dateutil python-jobspy
```

## After Installation

Once dependencies are installed, run:

```bash
# If using venv
source venv/bin/activate

# Analyze your resume
python3 main.py init --resume resume/your_resume.pdf

# Run job scan
python3 main.py scan

# View results
python3 main.py report
```

## Quick Test

To verify installation worked:

```bash
python3 -c "import openai, PyPDF2, pydantic; print('✅ All dependencies installed!')"
```
