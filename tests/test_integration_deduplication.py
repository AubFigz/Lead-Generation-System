import pytest
import pandas as pd
from integration_deduplication import integrate_and_deduplicate


@pytest.fixture
def sample_data():
    """
    Provides sample datasets for testing integration and deduplication.
    """
    data1 = pd.DataFrame({'name': ['A', 'B'], 'value': [1, 2]})
    data2 = pd.DataFrame({'name': ['B', 'C'], 'value': [2, 3]})
    return data1, data2


def test_integrate_and_deduplicate_basic(sample_data):
    """
    Test basic integration and deduplication functionality.
    """
    data1, data2 = sample_data
    deduped_data = integrate_and_deduplicate([data1, data2])

    # Check the number of rows after deduplication
    assert len(deduped_data) == 3, "Deduplicated dataset should have 3 rows"

    # Check that required columns are present
    assert 'name' in deduped_data.columns, "Column 'name' should exist in the deduplicated data"
    assert 'value' in deduped_data.columns, "Column 'value' should exist in the deduplicated data"


def test_integrate_and_deduplicate_empty_datasets():
    """
    Test handling of empty datasets.
    """
    empty_data1 = pd.DataFrame(columns=['name', 'value'])
    empty_data2 = pd.DataFrame(columns=['name', 'value'])
    deduped_data = integrate_and_deduplicate([empty_data1, empty_data2])

    # Check that the result is an empty DataFrame
    assert deduped_data.empty, "Result should be an empty DataFrame when all input datasets are empty"


def test_integrate_and_deduplicate_conflicting_duplicates():
    """
    Test handling of conflicting duplicate data.
    """
    data1 = pd.DataFrame({'name': ['A', 'B'], 'value': [1, 2]})
    data2 = pd.DataFrame({'name': ['B', 'A'], 'value': [3, 4]})
    deduped_data = integrate_and_deduplicate([data1, data2])

    # Check that the number of rows matches the unique 'name' values
    assert len(deduped_data) == 2, "Deduplicated dataset should have 2 unique rows"

    # Check that the conflict resolution logic is applied correctly
    assert deduped_data.loc[deduped_data['name'] == 'A', 'value'].iloc[
               0] == 4, "Conflict should resolve to the latest value"
    assert deduped_data.loc[deduped_data['name'] == 'B', 'value'].iloc[
               0] == 3, "Conflict should resolve to the latest value"


def test_integrate_and_deduplicate_varying_schemas():
    """
    Test handling of datasets with varying schemas.
    """
    data1 = pd.DataFrame({'name': ['A', 'B'], 'value': [1, 2]})
    data2 = pd.DataFrame({'name': ['C', 'D'], 'score': [3, 4]})
    deduped_data = integrate_and_deduplicate([data1, data2])

    # Check that columns are merged correctly
    assert 'name' in deduped_data.columns, "Column 'name' should exist in the deduplicated data"
    assert 'value' in deduped_data.columns, "Column 'value' should exist in the deduplicated data"
    assert 'score' in deduped_data.columns, "Column 'score' should exist in the deduplicated data"

    # Check for null handling in merged columns
    assert deduped_data['value'].isnull().sum() > 0, "Null values should exist for missing data in 'value' column"
    assert deduped_data['score'].isnull().sum() > 0, "Null values should exist for missing data in 'score' column"


def test_integrate_and_deduplicate_large_datasets():
    """
    Test handling of large datasets.
    """
    large_data1 = pd.DataFrame({'name': [f'Name{i}' for i in range(1000)], 'value': range(1000)})
    large_data2 = pd.DataFrame({'name': [f'Name{i}' for i in range(500, 1500)], 'value': range(500, 1500)})
    deduped_data = integrate_and_deduplicate([large_data1, large_data2])

    # Check that the deduplicated dataset has the correct number of rows
    assert len(deduped_data) == 1500, "Deduplicated dataset should have 1500 rows"

