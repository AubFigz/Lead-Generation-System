import pandas as pd
from data_preprocessing import clean_and_preprocess
import pytest

@pytest.fixture
def raw_data():
    """
    Fixture providing raw test data for preprocessing.
    """
    return pd.DataFrame({
        'name': [' Project A ', 'Project B!!!', None],
        'price': [100000, None, 500000],
        'area': [1500, 2000, 2500],
        'status': ['Available', None, 'Sold'],
        'text': ['This is a great project!', None, 'Highly recommended project!']
    })

def test_clean_and_preprocess_missing_values(raw_data):
    """
    Test that missing values are correctly handled.
    """
    cleaned_data = clean_and_preprocess(raw_data)
    assert cleaned_data.isnull().sum().sum() == 0, "Missing values should be handled"
    assert 'name' in cleaned_data.columns, "The 'name' column should exist after cleaning"

def test_clean_and_preprocess_outliers(raw_data):
    """
    Test that outliers are correctly handled.
    """
    # Inject an outlier into the raw data
    raw_data_with_outlier = raw_data.copy()
    raw_data_with_outlier.loc[0, 'price'] = 1e7  # Add a price outlier

    cleaned_data = clean_and_preprocess(raw_data_with_outlier)
    assert cleaned_data['price'].max() <= 500000, "Outliers should be clipped"

def test_clean_and_preprocess_text_cleaning(raw_data):
    """
    Test that text columns are correctly cleaned and standardized.
    """
    cleaned_data = clean_and_preprocess(raw_data)
    assert cleaned_data['name'].iloc[0] == "Project A", "Extra spaces and special characters should be removed"
    assert cleaned_data['name'].iloc[1] == "Project B", "Special characters should be removed"

def test_clean_and_preprocess_nlp_processing(raw_data):
    """
    Test that NLP-based processing is correctly applied.
    """
    cleaned_data = clean_and_preprocess(raw_data, enable_nlp=True, scoring_keywords=["great", "recommended"])
    assert 'sentiment' in cleaned_data.columns, "Sentiment analysis column should be added if NLP is enabled"
    assert 'lead_score' in cleaned_data.columns, "Lead scoring column should be added if NLP is enabled"
    assert cleaned_data['lead_score'].iloc[0] == "High Priority", "Text with keywords should be scored as 'High Priority'"

def test_clean_and_preprocess_column_types(raw_data):
    """
    Test that categorical and numeric columns are correctly processed.
    """
    cleaned_data = clean_and_preprocess(raw_data)
    assert cleaned_data['status'].dtype.name == 'category', "Status column should be converted to category"
    assert cleaned_data['price'].dtype.name == 'float64', "Price column should remain as a numeric type"

