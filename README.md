# Lead Generation System

## Overview
The Lead Generation System is a robust solution designed to automate the collection, processing, analysis, and management of business leads. By integrating data from diverse sources such as construction websites, real estate platforms, and social media, the system streamlines lead management workflows. It employs advanced tools and libraries to ensure efficiency, scalability, and reliability.

---

## Features
- **Automated Data Collection**: Gathers data from web scraping and APIs.
- **Data Cleaning and Preprocessing**: Ensures high-quality data.
- **Lead Scoring**: Prioritizes high-value leads using machine learning.
- **Visual Reporting**: Generates detailed insights with visualizations.
- **Web Interface**: User-friendly portal for lead management.
- **Database Maintenance**: Includes cleanup and backup functionalities.
- **Monitoring and Notifications**: Tracks system health and sends alerts.
- **Task Automation**: Schedules routine tasks dynamically.

---

## Requirements

### System Requirements
- Python 3.8 or higher
- PostgreSQL database
- Secure server environment for hosting the web application
- Reliable internet connection

### Software Requirements
- **Operating System**: Linux/Windows/MacOS
- **Dependencies**: Install required libraries from `requirements.txt`
- **Cloud Service Credentials**: AWS S3 and GCP for storage

### User Requirements
- Basic understanding of data management and web interfaces
- Access permissions to configure server and database

---

## Tools and Libraries
### Key Libraries
- **Data Collection**: `requests`, `BeautifulSoup`, `Selenium`, `Tweepy`
- **Data Preprocessing**: `Pandera`, `scikit-learn`, `MinMaxScaler`
- **Data Integration**: `fuzzywuzzy`
- **Visualization**: `matplotlib`, `plotly`
- **Database Management**: `psycopg2`, `SQLAlchemy`
- **Cloud Services**: `boto3`, `google-cloud-storage`
- **Monitoring and Scheduling**: `schedule`, `tenacity`
- **Web Application**: `Flask`
- **Notifications**: `smtplib`

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/lead-generation-system.git
   cd lead-generation-system
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the Environment**:
   - Edit `config.yaml` to include database credentials, API keys, and cloud storage settings.

5. **Initialize the Database**:
   ```bash
   python app.py  # Creates necessary tables
   ```

6. **Run the Application**:
   ```bash
   python app.py
   ```
   Access the web interface at `http://localhost:5000`.

---

## Usage

### Workflow
1. **Data Collection**: Run scripts to collect data from various sources.
   ```bash
   python Construction_DataCollection.py
   python RealEstate_DataCollection.py
   python Twitter_DataCollection.py
   ```
2. **Preprocessing**: Clean and preprocess the collected data.
   ```bash
   python data_preprocessing.py
   ```
3. **Integration and Deduplication**: Merge and clean datasets.
   ```bash
   python integration_deduplication.py
   ```
4. **Lead Scoring**: Prioritize leads with a machine learning model.
   ```bash
   python lead_scoring.py
   ```
5. **Analysis**: Generate detailed insights and visual reports.
   ```bash
   python lead_analysis.py
   ```
6. **Monitoring**: Ensure the health of APIs, scraping processes, and database connections.
   ```bash
   python api_usage_monitoring.py
   python scraping_process_monitoring.py
   python database_connection_monitoring.py
   ```
7. **Task Automation**: Schedule routine tasks.
   ```bash
   python task_scheduler.py
   ```
8. **Notifications**: Notify stakeholders and export data.
   ```bash
   python notifications.py
   ```

---

## Configuration

The project uses a `config.yaml` file for customizable settings, including:
- **Database**: Connection details and pool configuration
- **APIs**: Keys and parameters for external services
- **Logging**: File paths, levels, and rotation settings
- **Cloud Storage**: AWS S3 or GCP details
- **Task Scheduler**: Scripts and their schedules

---
Running Tests
This project includes comprehensive tests to ensure that all components of the Lead Generation System function as expected. Follow these steps to run the tests:

Prerequisites
Install pytest:

Ensure you have pytest installed for running tests:
bash
Copy code
pip install pytest
Install Coverage Tool (Optional):

To measure code coverage, install pytest-cov:
bash
Copy code
pip install pytest-cov
Test Dependencies:

Ensure all project dependencies from requirements.txt are installed:
bash
Copy code
pip install -r requirements.txt
Set Up the Environment:

If using environment variables, ensure your .env file is properly configured.
How to Run Tests
Run All Tests:

To execute all test cases:
bash
Copy code
pytest tests/
Run Tests Verbosely:

To see detailed output during test execution:
bash
Copy code
pytest tests/ -v
Run Specific Tests:

To run a specific test file (e.g., test_lead_scoring.py):
bash
Copy code
pytest tests/test_lead_scoring.py
Run Tests with Coverage:

To generate a code coverage report:
bash
Copy code
pytest --cov=your_project_directory tests/
Replace your_project_directory with the root folder of your project.
Generate an HTML Coverage Report:

To create an interactive HTML coverage report:
bash
Copy code
pytest --cov=your_project_directory --cov-report=html tests/
Open the generated htmlcov/index.html in a browser to view details.
Interpreting Results
PASS: Indicates the function or component passed all assertions and works as intended.
FAIL: Indicates an assertion failed. Check the traceback in the terminal for debugging.
SKIP: Indicates a test was intentionally skipped (e.g., environment-specific conditions).
Common Issues and Fixes
Database Connection Errors:

Ensure your PostgreSQL or SQLite instance is running and properly configured in conftest.py.
Missing Dependencies:

Run:
bash
Copy code
pip install -r requirements.txt
Environment Variables:

Ensure sensitive variables (e.g., API keys) are set in a .env file or your system environment.
Test Data Conflicts:

Some tests rely on isolated environments (e.g., SQLite in-memory). Ensure no external data conflicts exist.
