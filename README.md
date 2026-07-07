# Lead Generation System

## **Introduction**
The Lead Generation System is a comprehensive, scalable platform designed to automate and optimize the process of acquiring, scoring, and managing leads. By leveraging modern technologies such as machine learning, data processing, and robust backend services, this system streamlines workflows for businesses seeking to enhance their lead management capabilities. It provides features such as automated data collection, lead scoring, and a user-friendly interface for managing leads, all while ensuring system reliability through robust monitoring and task automation.

---

## **Project Overview**
### **Goals and Use Cases**
- Automate the process of collecting lead data from multiple sources, including APIs, social media, and websites.
- Score and prioritize leads using machine learning models to improve conversion rates.
- Provide a centralized system for managing, analyzing, and reporting on leads.
- Enable routine operations such as database cleanup and report generation through automated tasks.
- Ensure system health with real-time monitoring and logging.

### **Features**
- **Automated Data Collection**: Integrates with APIs, scrapes data from real estate and construction platforms, and performs sentiment analysis on Twitter data.
- **Data Cleaning and Enrichment**: Processes raw data to ensure high quality and usability, with features such as deduplication and NLP-based analysis.
- **Lead Scoring**: Utilizes machine learning models to assign scores to leads, enabling prioritization.
- **User Interface**: Offers a responsive web application for managing and visualizing leads.
- **Notifications and Reporting**: Sends periodic email reports and allows data export to CSV.
- **Task Scheduling**: Automates recurring operations such as cleanup and reporting.
- **System Monitoring**: Tracks system performance and logs critical events for troubleshooting.

---

## **Project Structure**
```
Lead Generation System
├── .github
│   └── workflows
│       └── ci.yml
├── .venv
├── etc
│   └── nginx
│       └── conf.d
│           └── nginx.conf
├── scripts
│   ├── cleanup_old_leads.py
│   └── send_weekly_report.py
├── static
│   ├── script.js
│   └── style.css
├── templates
│   ├── 404.html
│   ├── 50x.html
│   ├── edit_lead.html
│   ├── index.html
│   ├── login.html
│   ├── password_reset.html
│   ├── password_reset_confirm.html
│   ├── profile.html
│   ├── register.html
│   └── success.html
├── tests
│   ├── conftest.py
│   ├── test_api_usage_monitoring.py
│   ├── test_app.py
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_data_preprocessing.py
│   ├── test_database_management.py
│   ├── test_integration_deduplication.py
│   ├── test_lead_scoring.py
│   └── test_task_scheduler.py
├── api_usage_monitoring.py
├── app.py
├── audit_logging.py
├── auth.py
├── backup_database.py
├── build_frontend.py
├── config.yaml
├── Construction_DataCollection.py
├── data_preprocessing.py
├── database_connection_monitoring.py
├── database_management.py
├── docker-compose.yml
├── Dockerfile
├── health_check.py
├── integration_deduplication.py
├── lead_analysis.py
├── lead_scoring.py
├── monitoring.py
├── notifications.py
├── RealEstate_DataCollection.py
├── requirements.txt
├── scraping_process_monitoring.py
├── seed_data.py
├── setup_directories.py
├── task_scheduler.py
└── Twitter_DataCollection.py
```

---

## **Requirements**
### **Prerequisites**:
- Python 3.8+
- PostgreSQL
- Docker and Docker Compose
- Git

### **Python Dependencies**:
Install required libraries using:
```
pip install -r requirements.txt
```

### **Key Dependencies**:
- Flask
- SQLAlchemy
- Pandas
- Scikit-learn
- Requests
- pytest
- schedule

---

## **File Explanations**

### **1. Core Functionality**
- **`app.py`**:
  - Initializes the Flask application.
  - Handles user registration, authentication, and API endpoints for managing leads.

- **`auth.py`**:
  - Implements secure password hashing and verification for user authentication.

- **`config.yaml`**:
  - Contains environment-specific configurations, including database credentials and API keys.

- **`audit_logging.py`**:
  - Logs user actions, such as login attempts and lead modifications, for auditing.

- **`backup_database.py`**:
  - Automates database backup processes to ensure data safety.

### **2. Data Collection**
- **`api_usage_monitoring.py`**:
  - Monitors API call limits and implements retry mechanisms.

- **`Construction_DataCollection.py`** and **`RealEstate_DataCollection.py`**:
  - Scrapes construction and real estate project data.

- **`Twitter_DataCollection.py`**:
  - Collects and processes tweets, performing sentiment analysis and keyword extraction.

### **3. Data Processing**
- **`data_preprocessing.py`**:
  - Cleans raw data, handles missing values, and enriches it with NLP features.

- **`integration_deduplication.py`**:
  - Merges datasets from multiple sources and removes duplicates.

### **4. Machine Learning**
- **`lead_scoring.py`**:
  - Applies a Random Forest model to score leads based on predefined metrics.

- **`lead_analysis.py`**:
  - Generates statistical insights and visualizations from lead data.

### **5. System Monitoring and Task Management**
- **`task_scheduler.py`**:
  - Schedules recurring tasks like database cleanup and report generation.

- **`health_check.py`** and **`monitoring.py`**:
  - Monitor resource utilization and system health.

### **6. Frontend**
- **`static/`**:
  - Contains JavaScript (`script.js`) and CSS (`style.css`) files for frontend interactivity and styling.

- **Templates**:
  - HTML templates for rendering the web interface (e.g., `index.html`, `edit_lead.html`).

### **7. Testing**
- **`tests/`**:
  - Contains unit and integration tests for components like authentication, data preprocessing, and lead scoring.

---

## **Setup Instructions**

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd lead-generation-system
```

### **2. Configure Environment Variables**
- Create a `.env` file based on the provided `.env.example`.
- Update credentials for PostgreSQL, API keys, and other settings.

### **3. Build and Run the System with Docker**
```bash
docker-compose up --build
```

### **4. Access the Application**
- The web interface will be available at `http://localhost:5000`.

### **5. Run Tests**
```bash
pytest tests/
```

---

## **Getting Started & Testing**

### Prerequisites
- Python 3.10+
- (optional) PostgreSQL for full end-to-end runs. The automated tests use an in-memory SQLite database and need no external services.

### Setup
```bash
git clone <repo-url> && cd Lead-Generation-System
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your own values
```

Configuration is loaded via `config_loader.py`, which expands `${VAR}` / `${VAR:-default}` references in `config.yaml` from your `.env`, so secrets stay out of the YAML.

### Run the tests
```bash
pytest        # 48 tests, all passing
```

### Run the API
```bash
flask --app app run         # or: python app.py
```
The service exposes authentication and lead CRUD endpoints (interactive docs at `/apidocs`). The frontend in `templates/` and `static/` is served by nginx in the Docker setup (`docker-compose up`).

---

## **Known Limitations**
- **Twitter/X collection uses the X API v2** (`tweepy.Client` + `search_recent_tweets`). Since Feb 2026 the X API has no free tier for new developers; search is billed pay-per-use, so a funded Bearer Token (`TWITTER_BEARER_TOKEN`) and a spending cap are required to fetch live data. The rest of the pipeline runs independently of it. Recent search covers the last 7 days.
- The real-estate and construction Selenium collectors target specific external websites and may need selector updates if those sites change.
- Cloud (AWS/GCP) and email features require valid credentials in `.env` and are disabled by default.

---

## **Usage Instructions**
1. **Log In**: Register or log in via the web interface.
2. **Add Leads**: Use the interface or API to add leads.
3. **View and Edit Leads**: Navigate to the leads table, where you can edit or delete entries.
4. **Monitor System**: Check logs and health metrics via integrated monitoring tools.
5. **Generate Reports**: Receive weekly reports via email or download lead data as CSV.

---

## **Security Notes**
- Credentials live in `.env` (never commit it); this repo ships only `.env.example` with placeholder values.
- Use HTTPS to encrypt communication between the client and server.
- Implement role-based access control for user management.

---

## **Future Enhancements**
- Add real-time dashboards for monitoring lead activity.
- Incorporate additional machine learning models for better lead prioritization.
- Expand integration with CRM platforms for seamless lead management.

---
