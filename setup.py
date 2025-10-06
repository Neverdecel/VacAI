from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vacai",
    version="0.1.0",
    description="AI-Powered Job Search Automation - Automate your job search with AI matching and scoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="VacAI Contributors",
    url="https://github.com/YOUR_USERNAME/vacai",
    project_urls={
        "Bug Reports": "https://github.com/YOUR_USERNAME/vacai/issues",
        "Source": "https://github.com/YOUR_USERNAME/vacai",
        "Documentation": "https://github.com/YOUR_USERNAME/vacai/tree/main/docs",
    },
    packages=find_packages(),
    install_requires=[
        "openai>=1.50.0",
        "python-dotenv>=1.0.0",
        "python-jobspy>=1.1.80",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "python-dateutil>=2.8.0",
        "PyPDF2>=3.0.0",
        "python-telegram-bot>=21.0.0",
    ],
    entry_points={
        'console_scripts': [
            'vacai=src.cli.commands:cli',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="job-search ai automation openai career job-hunting",
    python_requires=">=3.10",
    license="MIT",
)
