"""
X (Twitter) v2 lead collector.

Migrated from the retired v1.1 search endpoint to X API v2 (tweepy.Client +
search_recent_tweets). Recent search covers the last 7 days. As of 2026 the X API has
no free tier for new developers: search is billed pay-per-use (about $0.005 per post
returned, ~2M reads/month cap), so a funded Bearer Token and a spending cap are required
to fetch live data. The rest of the pipeline runs independently of this module.
"""
import tweepy
import psycopg2
import logging
from textblob import TextBlob
from tenacity import retry, stop_after_attempt, wait_exponential
from pytz import timezone
import boto3
from google.cloud import storage
from logging.handlers import RotatingFileHandler
import pandas as pd
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


def authenticate_twitter(api_keys):
    """v2 app-only authentication. Only a Bearer Token is needed for search/read."""
    client = tweepy.Client(bearer_token=api_keys["bearer_token"], wait_on_rate_limit=True)
    logging.info("X API v2 client authenticated.")
    return client


def localize_timestamp(timestamp, tz_string):
    try:
        return timestamp.astimezone(timezone(tz_string))
    except Exception as e:
        logging.error(f"Error localizing timestamp: {e}")
        raise


def analyze_sentiment_or_score(tweet_text, enable_sentiment_analysis, enable_lead_scoring, scoring_keywords=None):
    sentiment_score = None
    lead_score = None
    if enable_sentiment_analysis:
        polarity = TextBlob(tweet_text).sentiment.polarity
        sentiment_score = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
    if enable_lead_scoring:
        scoring_keywords = scoring_keywords or []
        lead_score = "High Priority" if any(k.lower() in tweet_text.lower() for k in scoring_keywords) else "Low Priority"
    return {"sentiment": sentiment_score, "lead_priority": lead_score}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
def search_tweets(client, query, geolocation, count, enable_sentiment_analysis,
                  enable_lead_scoring, scoring_keywords, config):
    """v2 recent search (last 7 days). Paginates, resolves author usernames via
    expansions, and stops once `count` tweets have been collected."""
    q = f"{query} lang:en -is:retweet"

    # Optional geo filter. v2 has no 'geocode' param; use the point_radius operator.
    # config stores "lat,lon,radius"; v2 wants [lon lat radius], radius <= 25mi.
    if geolocation:
        try:
            lat, lon, radius = [p.strip() for p in geolocation.split(",")]
            q += f" point_radius:[{lon} {lat} {radius}]"
        except ValueError:
            logging.warning("Ignoring malformed geolocation; expected 'lat,lon,radius'.")

    results = []
    paginator = tweepy.Paginator(
        client.search_recent_tweets,
        query=q,
        max_results=100,
        tweet_fields=["created_at", "author_id", "lang"],
        expansions=["author_id"],
        user_fields=["username"],
    )
    for page in paginator:
        if not page.data:
            continue
        users = {u.id: u for u in (page.includes.get("users", []) if page.includes else [])}
        for tweet in page.data:
            score = analyze_sentiment_or_score(tweet.text, enable_sentiment_analysis,
                                               enable_lead_scoring, scoring_keywords)
            author = users.get(tweet.author_id)
            screen_name = author.username if author else str(tweet.author_id)
            created = localize_timestamp(tweet.created_at, config["system"]["timezone"])
            results.append((screen_name, tweet.text, created,
                            score["sentiment"], score["lead_priority"]))
            if len(results) >= count:
                logging.info(f"Fetched {len(results)} tweets for query: {query}")
                return results
    logging.info(f"Fetched {len(results)} tweets for query: {query}")
    return results


def store_tweets_in_db(tweets, db_config):
    if not tweets:
        logging.info("No tweets to store in the database.")
        return
    conn = None
    try:
        conn = psycopg2.connect(host=db_config['host'], database=db_config['database'],
                                user=db_config['user'], password=db_config['password'])
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS twitter_leads (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255),
                tweet_text TEXT,
                created_at TIMESTAMP,
                sentiment VARCHAR(50),
                lead_priority VARCHAR(50)
            )
        ''')
        cur.executemany(
            "INSERT INTO twitter_leads (username, tweet_text, created_at, sentiment, lead_priority) "
            "VALUES (%s, %s, %s, %s, %s)", tweets)
        conn.commit()
        logging.info(f"Successfully stored {len(tweets)} tweets in the database.")
        cur.close()
    except Exception as e:
        logging.error(f"Error storing tweets in the database: {e}")
    finally:
        if conn is not None:
            conn.close()


def save_to_cloud(tweets, cloud_storage, table_name):
    if not tweets or not cloud_storage.get('enabled', False):
        return
    file_name = f"{table_name}.csv"
    try:
        df = pd.DataFrame(tweets, columns=["username", "tweet_text", "created_at", "sentiment", "lead_priority"])
        df.to_csv(file_name, index=False)
        if cloud_storage['provider'] == 'aws':
            s3 = boto3.client('s3', region_name=cloud_storage.get('region', 'us-east-1'))
            s3.upload_file(file_name, cloud_storage['bucket_name'], file_name)
            logging.info(f"Uploaded to AWS S3 bucket {cloud_storage['bucket_name']} as {file_name}.")
        elif cloud_storage['provider'] == 'gcp':
            client = storage.Client(project=cloud_storage.get('gcp_project'))
            client.bucket(cloud_storage['bucket_name']).blob(file_name).upload_from_filename(file_name)
            logging.info(f"Uploaded to GCP bucket {cloud_storage['bucket_name']} as {file_name}.")
    except Exception as e:
        logging.error(f"Error uploading to cloud storage: {e}")


if __name__ == "__main__":
    config = load_config()
    setup_logging(config)

    tw = config["twitter"]
    client = authenticate_twitter({"bearer_token": tw["bearer_token"]})

    keywords = tw.get("query_keywords", [])
    query = "(" + " OR ".join(f'"{k}"' for k in keywords) + ")"

    tweets = search_tweets(
        client, query, tw.get("geolocation"), count=100,
        enable_sentiment_analysis=config["advanced"]["enable_sentiment_analysis"],
        enable_lead_scoring=True,
        scoring_keywords=keywords,
        config=config,
    )
    store_tweets_in_db(tweets, config["database"])
    save_to_cloud(tweets, config["advanced"]["cloud_storage"], "twitter_leads")
