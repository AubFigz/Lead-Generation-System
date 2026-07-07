import pandas as pd
import numpy as np
import re
import logging
import yaml
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from textblob import TextBlob
from logging.handlers import RotatingFileHandler
from config_loader import load_config

try:
    from pandera.pandas import DataFrameSchema, Column, Check
    from pandera.errors import SchemaErrors
except Exception:  # pragma: no cover - pandera is optional for the core cleaning path
    DataFrameSchema = Column = Check = None
    SchemaErrors = Exception


def setup_logging(config):
    handler = RotatingFileHandler(
        config['logging']['file'],
        maxBytes=int(config['logging']['max_file_size'].replace('MB', '')) * 1024 * 1024,
        backupCount=config['logging']['backup_count'],
    )
    logging.basicConfig(
        level=logging.DEBUG if config.get('environment') == 'development' else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


def fetch_data_in_batches(table_name, db_config, batch_size=5000):
    engine = create_engine(
        f"postgresql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}/{db_config['database']}"
    )
    return pd.read_sql(f"SELECT * FROM {table_name};", engine, chunksize=batch_size)


def validate_schema(dataframe, schema):
    try:
        return schema.validate(dataframe)
    except SchemaErrors as e:
        logging.error(f"Schema validation errors:\n{e}")
        raise


def _clean_text(value):
    """Strip whitespace and remove special characters, keeping letters, digits, spaces."""
    text = re.sub(r'[^0-9A-Za-z\s]', '', str(value))
    return re.sub(r'\s+', ' ', text).strip()


def clean_and_preprocess(dataframe, enable_nlp=False, scoring_keywords=None):
    """Clean a raw lead dataframe: dedupe, impute missing values, standardize text,
    clip and scale numerics, optionally run NLP sentiment/priority scoring, and cast
    categorical columns to the category dtype."""
    df = dataframe.drop_duplicates().copy()

    text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    # impute missing values
    for col in text_cols:
        df[col] = df[col].fillna('Unknown')
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())

    # standardize text
    for col in text_cols:
        df[col] = df[col].apply(_clean_text)

    # clip outliers (IQR) then scale numerics to [0, 1]
    for col in numeric_cols:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        df[col] = np.clip(df[col], q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    if numeric_cols:
        df[numeric_cols] = MinMaxScaler().fit_transform(df[numeric_cols])

    # optional NLP enrichment
    if enable_nlp and 'text' in df.columns:
        keywords = [k.lower() for k in (scoring_keywords or [])]
        df['sentiment'] = df['text'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
        df['lead_score'] = df['text'].apply(
            lambda x: "High Priority" if any(k in str(x).lower() for k in keywords) else "Low Priority"
        )

    # cast categorical (text) columns to category dtype
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].astype('category')

    return df


def save_cleaned_data(dataframe, table_name, db_config):
    engine = create_engine(
        f"postgresql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}/{db_config['database']}"
    )
    dataframe.to_sql(table_name, engine, if_exists='replace', index=False)
