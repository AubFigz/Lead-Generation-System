import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import yaml
import os
from datetime import datetime
import plotly.express as px
from sqlalchemy import create_engine
from notifications import notify_stakeholders
import boto3
from logging.handlers import RotatingFileHandler
import pytz


# Setup logging
def setup_logging(config):
    handler = RotatingFileHandler(
        config['logging']['file'],
        maxBytes=int(config['logging']['max_file_size'].replace('MB', '')) * 1024 * 1024,
        backupCount=config['logging']['backup_count']
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[handler, logging.StreamHandler()]
    )


# Load configuration
def load_config(config_file="config.yaml"):
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        logging.info("Configuration file loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {e}")
        raise


# Validate and clean data
def validate_and_clean_data(dataframe):
    required_columns = ['lead_score']
    for col in required_columns:
        if col not in dataframe.columns:
            raise ValueError(f"Required column '{col}' is missing in the dataset.")
    dataframe.dropna(subset=required_columns, inplace=True)
    logging.info(f"Validated dataset with {len(dataframe)} rows.")
    return dataframe


# Generate summary statistics
def generate_summary_statistics(dataframe):
    summary = dataframe.describe().transpose()
    logging.info("Summary statistics generated.")
    return summary


# Generate visualizations
def generate_visualizations(dataframe, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Lead Score Distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(dataframe['lead_score'], kde=True, bins=20)
    plt.title('Lead Score Distribution')
    plt.xlabel('Lead Score')
    plt.ylabel('Frequency')
    plt.tight_layout()
    dist_file = os.path.join(output_dir, "lead_score_distribution.png")
    plt.savefig(dist_file)
    logging.info(f"Lead score distribution plot saved to {dist_file}.")

    # Interactive Plot
    interactive_file = os.path.join(output_dir, "lead_score_distribution.html")
    fig = px.histogram(dataframe, x='lead_score', title='Interactive Lead Score Distribution')
    fig.write_html(interactive_file)
    logging.info(f"Interactive lead score distribution plot saved to {interactive_file}.")

    return [dist_file, interactive_file]


# Analyze high-priority leads
def analyze_high_priority_leads(dataframe, output_dir):
    high_priority = dataframe[dataframe['lead_score'] > 0.8]
    plt.figure(figsize=(10, 6))
    sns.countplot(data=high_priority, x='source', order=high_priority['source'].value_counts().index)
    plt.title('High Priority Leads by Source')
    plt.xlabel('Source')
    plt.ylabel('Count')
    plt.tight_layout()
    file_path = os.path.join(output_dir, "high_priority_leads_by_source.png")
    plt.savefig(file_path)
    logging.info(f"High priority leads by source plot saved to {file_path}.")
    return file_path


# Save reports to cloud storage
def upload_reports_to_cloud(output_dir, cloud_config):
    if not cloud_config.get('enabled', False):
        return
    try:
        s3 = boto3.client('s3', region_name=cloud_config['region'])
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            s3.upload_file(file_path, cloud_config['bucket_name'], file)
            logging.info(f"Uploaded {file} to S3 bucket {cloud_config['bucket_name']}.")
    except Exception as e:
        logging.error(f"Error uploading reports to cloud: {e}")


# Generate summary report
def generate_summary_report(output_dir, summary_stats, top_leads_file, plots):
    report_file = os.path.join(output_dir, "lead_analysis_report.md")
    with open(report_file, "w") as report:
        report.write("# Lead Analysis Report\n")
        report.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        report.write("## Summary Statistics\n")
        report.write(summary_stats.to_markdown())
        report.write("\n\n## Top 10 Leads\n")
        report.write(f"See: {top_leads_file}\n\n")
        for plot in plots:
            report.write(f"![{os.path.basename(plot)}]({plot})\n")
    logging.info(f"Summary report saved to {report_file}.")
    return report_file


# Main flow
if __name__ == "__main__":
    config = load_config()
    setup_logging(config)

    db_config = config['database']
    output_dir = config['export']['directory']
    cloud_config = config['advanced']['cloud_storage']

    # Fetch data from database
    engine = create_engine(
        f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
    )
    query = "SELECT * FROM scored_leads;"
    dataframe = pd.read_sql(query, engine)

    # Validate and clean data
    dataframe = validate_and_clean_data(dataframe)

    # Generate summary statistics
    summary_stats = generate_summary_statistics(dataframe)

    # Save top 10 leads
    top_leads = dataframe.nlargest(10, 'lead_score')
    top_leads_file = os.path.join(output_dir, "top_10_leads.csv")
    top_leads.to_csv(top_leads_file, index=False)
    logging.info(f"Top 10 leads saved to {top_leads_file}.")

    # Generate visualizations
    plots = generate_visualizations(dataframe, output_dir)

    # Analyze high-priority leads
    high_priority_plot = analyze_high_priority_leads(dataframe, output_dir)

    # Upload reports to cloud storage
    upload_reports_to_cloud(output_dir, cloud_config)

    # Generate summary report
    summary_report = generate_summary_report(output_dir, summary_stats, top_leads_file, plots)

    # Send notification
    notify_stakeholders(
        config['notifications']['recipient_emails'],
        "Lead Analysis Report Generated",
        f"The lead analysis report is available at {summary_report}.",
        config
    )
