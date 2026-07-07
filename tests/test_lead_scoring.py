import pytest
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from lead_scoring import score_leads


@pytest.fixture
def test_data():
    """
    Provides sample test data for lead scoring.
    """
    return pd.DataFrame({
        'price': [100000, 200000, 300000],
        'area': [1200, 1500, 1800],
        'status': ['Available', 'Sold', 'Available']
    })


@pytest.fixture
def mock_model_path(tmp_path):
    """
    Creates and saves a mock model for testing.
    """
    model = RandomForestClassifier()
    # Generate some mock training data
    X_train = pd.DataFrame({
        'price': [100000, 200000, 300000],
        'area': [1200, 1500, 1800],
        'status_Available': [1, 0, 1],
        'status_Sold': [0, 1, 0]
    })
    y_train = [1, 0, 1]  # Mock labels
    model.fit(X_train, y_train)

    model_path = tmp_path / "test_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    return str(model_path)


def test_score_leads_basic(test_data, mock_model_path):
    """
    Tests basic lead scoring functionality.
    """
    features = ['price', 'area', 'status']
    scored_data = score_leads(test_data, features, mock_model_path)

    # Check that the 'lead_score' column is added
    assert 'lead_score' in scored_data.columns, "'lead_score' column should be added to the dataframe"

    # Ensure all lead scores are non-null
    assert all(scored_data['lead_score'].notnull()), "All rows should have a non-null lead score"


def test_score_leads_missing_features(test_data, mock_model_path):
    """
    Tests lead scoring when some features are missing.
    """
    incomplete_data = test_data.drop(columns=['area'])
    features = ['price', 'area', 'status']

    with pytest.raises(KeyError):
        score_leads(incomplete_data, features, mock_model_path)


def test_score_leads_empty_dataset(mock_model_path):
    """
    Tests lead scoring with an empty dataset.
    """
    empty_data = pd.DataFrame(columns=['price', 'area', 'status'])
    features = ['price', 'area', 'status']

    scored_data = score_leads(empty_data, features, mock_model_path)
    assert scored_data.empty, "The returned dataframe should be empty"


def test_score_leads_invalid_model(test_data, tmp_path):
    """
    Tests lead scoring with an invalid model file.
    """
    features = ['price', 'area', 'status']
    invalid_model_path = "./invalid_model.pkl"

    # Create a mock invalid model file
    with open(invalid_model_path, 'w') as f:
        f.write("This is not a valid model")

    with pytest.raises(Exception):
        score_leads(test_data, features, invalid_model_path)


def test_score_leads_varying_data_distribution(mock_model_path):
    """
    Tests lead scoring with varying data distributions.
    """
    varied_data = pd.DataFrame({
        'price': [50000, 700000, 1000000],
        'area': [800, 3500, 5000],
        'status': ['Available', 'Sold', 'Available']
    })
    features = ['price', 'area', 'status']

    scored_data = score_leads(varied_data, features, mock_model_path)

    # Ensure all lead scores are calculated
    assert all(scored_data['lead_score'].notnull()), "All rows should have a non-null lead score"


def test_score_leads_unseen_status(test_data, mock_model_path):
    """
    Tests lead scoring when an unseen category is present in the 'status' feature.
    """
    test_data_with_unseen_status = test_data.copy()
    test_data_with_unseen_status.loc[0, 'status'] = 'Pending'

    features = ['price', 'area', 'status']

    with pytest.raises(ValueError):
        score_leads(test_data_with_unseen_status, features, mock_model_path)
