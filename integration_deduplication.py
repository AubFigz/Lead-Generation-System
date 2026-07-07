import pandas as pd
from fuzzywuzzy import fuzz, process
from sqlalchemy import create_engine
import logging
import yaml
import boto3
from logging.handlers import RotatingFileHandler
from config_loader import load_config


def setup_logging(config):
    handler = RotatingFileHandler(
        config['logging']['file'],
        maxBytes=int(config['logging']['max_file_size'].replace('MB', '')) * 1024 * 1024,
        backupCount=config['logging']['backup_count'],
    )
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[handler, logging.StreamHandler()])
    logging.info("Logging setup complete.")


def integrate_and_deduplicate(datasets, source_labels=None, key_columns=None,
                              dedup_priority=None, enable_fuzzy=False,
                              fuzzy_threshold=85, custom_rules=None, keep='last'):
    """Combine several lead datasets and deduplicate them.

    - `source_labels` (optional) tags each row with its origin.
    - By default the identity key is the first column common to every dataset,
      and duplicates resolve to the LAST occurrence (latest source wins).
    - Missing values are preserved as NaN so callers can see schema gaps.
    """
    if not datasets:
        return pd.DataFrame()

    if source_labels is not None:
        if len(datasets) != len(source_labels):
            raise ValueError("The number of datasets must match the number of source labels.")
        combined = pd.concat(datasets, keys=source_labels, names=['source']).reset_index(level=0)
    else:
        combined = pd.concat(datasets, ignore_index=True)

    if combined.empty:
        return combined

    if custom_rules and 'combine_fields' in custom_rules:
        combined['dedup_key'] = combined[custom_rules['combine_fields']].astype(str).agg(' '.join, axis=1)
        key_columns = ['dedup_key'] if key_columns is None else key_columns + ['dedup_key']

    if key_columns is None:
        common = [c for c in datasets[0].columns if all(c in df.columns for df in datasets)]
        key_columns = common[:1]  # first shared column is the identity key
    key_columns = [c for c in key_columns if c in combined.columns]

    if dedup_priority and 'source' in combined.columns:
        combined['__priority'] = combined['source'].map(dedup_priority)
        combined = combined.sort_values('__priority')

    if enable_fuzzy:
        logging.info(f"Applying fuzzy matching with threshold {fuzzy_threshold}.")
        for col in key_columns:
            if combined[col].dtype == object:
                uniques = list(combined[col].dropna().unique())

                def _canonical(x):
                    if not isinstance(x, str):
                        return x
                    match = process.extractOne(x, uniques, scorer=fuzz.ratio,
                                               score_cutoff=fuzzy_threshold)
                    return match[0] if match else x

                combined[col] = combined[col].apply(_canonical)

    if key_columns:
        combined = combined.drop_duplicates(subset=key_columns, keep=keep)

    if '__priority' in combined.columns:
        combined = combined.drop(columns='__priority')

    return combined.reset_index(drop=True)


def optimize_memory_usage(dataframe):
    for col in dataframe.select_dtypes(include=['object']).columns:
        dataframe[col] = dataframe[col].astype('category')
    return dataframe


def save_to_database(dataframe, table_name, db_config):
    try:
        engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}/{db_config['database']}"
        )
        dataframe.to_sql(table_name, engine, if_exists='replace', index=False)
        logging.info(f"Data successfully saved to table: {table_name}")
    except Exception as e:
        logging.error(f"Error saving to database table {table_name}: {e}")
        raise


def save_to_cloud(dataframe, bucket_name, file_name, region, file_format='csv', chunk_size=10000):
    try:
        s3 = boto3.client('s3', region_name=region)
        if file_format == 'csv':
            dataframe.to_csv(file_name, index=False)
        elif file_format == 'parquet':
            dataframe.to_parquet(file_name, index=False)
        s3.upload_file(file_name, bucket_name, file_name)
        logging.info(f"Data uploaded to S3 bucket {bucket_name} as {file_name}.")
    except Exception as e:
        logging.error(f"Error uploading to S3: {e}")


def integrate_and_save(datasets, source_labels, db_config, output_table_name, config, key_columns=None):
    adv = config.get('advanced', {})
    combined = integrate_and_deduplicate(
        datasets, source_labels, key_columns,
        adv.get('deduplication_priority', {}), adv.get('enable_fuzzy_deduplication', False),
        adv.get('fuzzy_matching_threshold', 85), adv.get('custom_deduplication_rules', {}),
    )
    combined = optimize_memory_usage(combined)
    save_to_database(combined, output_table_name, db_config)
    return combined
