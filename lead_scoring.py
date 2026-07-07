import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.metrics import roc_auc_score, classification_report
import yaml
import logging
from sqlalchemy import create_engine
import joblib
from datetime import datetime
import pytz
import boto3
from config_loader import load_config


def setup_logging(config):
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(config['logging']['file']), logging.StreamHandler()],
        )
    except Exception as e:
        logging.error(f"Error setting up logging: {e}")
        raise


def fetch_data_from_db(table_name, db_config):
    try:
        engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        dataframe = pd.read_sql(f"SELECT * FROM {table_name};", engine)
        logging.info(f"Fetched {len(dataframe)} rows from table {table_name}.")
        return dataframe
    except Exception as e:
        logging.error(f"Error fetching data from {table_name}: {e}")
        raise


def train_model(dataframe, feature_columns, model_path):
    """Train a lead-scoring model from labeled data and persist it. Categorical
    features are one-hot encoded so the saved model's feature names are explicit."""
    df = dataframe.copy()
    df['relevant'] = df['price'].apply(lambda x: 1 if x != 'N/A' else 0)
    X = pd.get_dummies(df[feature_columns])
    y = df['relevant']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    if len(set(y_test)) > 1:
        roc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
        logging.info(f"Model trained with ROC-AUC: {roc:.2f}")
    joblib.dump(model, model_path)
    logging.info(f"Model saved to {model_path}.")
    return model


def score_leads(dataframe, feature_columns, model_path):
    """Score leads with a pre-trained model.

    - Missing feature columns raise KeyError.
    - An empty input returns an empty frame (no scoring possible).
    - Categoricals are one-hot encoded and aligned to the model's training columns;
      a category the model never saw raises ValueError rather than scoring silently.
    """
    missing = [c for c in feature_columns if c not in dataframe.columns]
    if missing:
        raise KeyError(f"Missing feature columns: {missing}")

    df = dataframe.copy()
    if df.empty:
        df['lead_score'] = pd.Series(dtype=float)
        return df

    model = joblib.load(model_path)  # invalid model file raises here

    X = df[feature_columns].copy()
    categorical = X.select_dtypes(include=['object', 'string', 'category']).columns.tolist()
    X_encoded = pd.get_dummies(X, columns=categorical)

    expected = list(getattr(model, 'feature_names_in_', X_encoded.columns))
    unseen = [c for c in X_encoded.columns if c not in expected]
    if unseen:
        raise ValueError(f"Unseen categories produced unknown columns: {unseen}")

    X_aligned = X_encoded.reindex(columns=expected, fill_value=0)
    df['lead_score'] = model.predict_proba(X_aligned)[:, 1]
    logging.info("Lead scoring completed successfully.")
    return df


def save_scores_to_db(dataframe, table_name, db_config):
    try:
        engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        dataframe.to_sql(table_name, engine, if_exists='replace', index=False)
        logging.info(f"Scored leads saved to table {table_name}.")
    except Exception as e:
        logging.error(f"Error saving scores to {table_name}: {e}")
        raise


def upload_model_to_cloud(model_path, cloud_config):
    if not cloud_config.get('enabled', False):
        logging.info("Cloud storage is disabled in the configuration.")
        return
    if cloud_config.get('provider') == 'aws':
        s3 = boto3.client('s3', region_name=cloud_config['region'])
        try:
            s3.upload_file(model_path, cloud_config['bucket_name'], os.path.basename(model_path))
            logging.info(f"Model uploaded to AWS S3 bucket {cloud_config['bucket_name']}.")
        except Exception as e:
            logging.error(f"Error uploading model to AWS S3: {e}")
            raise
    else:
        raise ValueError(f"Unsupported cloud provider: {cloud_config.get('provider')}")


def localize_timestamp(timezone):
    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')


if __name__ == "__main__":
    config = load_config()
    setup_logging(config)
    db_config = config['database']
    features = config['advanced'].get('scoring_features', ['price', 'area', 'status'])
    model_path = config['advanced'].get('scoring_model_path', './models/lead_scoring_model.pkl')
    data = fetch_data_from_db(config['preprocessing']['tables']['real_estate_leads'], db_config)
    train_model(data, features, model_path)
    scored = score_leads(data, features, model_path)
    save_scores_to_db(scored, "scored_leads", db_config)
