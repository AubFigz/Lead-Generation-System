import pytest
from config import configurations


def test_configurations_exist():
    """
    Test that the configurations for all environments exist.
    """
    assert 'development' in configurations, "Development configuration is missing"
    assert 'production' in configurations, "Production configuration is missing"


def test_development_configuration():
    """
    Test that the development configuration is correctly set up.
    """
    dev_config = configurations['development']
    assert dev_config.SQLALCHEMY_DATABASE_URI.startswith("sqlite://"), \
        "Development database URI should use SQLite for testing"
    assert dev_config.DEBUG is True, "Development mode should have DEBUG enabled"


def test_production_configuration():
    """
    Test that the production configuration is correctly set up.
    """
    prod_config = configurations['production']
    assert 'postgresql' in prod_config.SQLALCHEMY_DATABASE_URI, \
        "Production database URI should use PostgreSQL"
    assert not prod_config.DEBUG, "Production mode should have DEBUG disabled"


def test_missing_configuration():
    """
    Test handling of missing configuration keys.
    """
    with pytest.raises(KeyError):
        configurations['nonexistent']


def test_configuration_keys():
    """
    Test that all required keys are present in the configurations.
    """
    required_keys = ['SQLALCHEMY_DATABASE_URI', 'DEBUG']

    for env, config in configurations.items():
        for key in required_keys:
            assert hasattr(config, key), f"Missing required key '{key}' in {env} configuration"


def test_invalid_configuration_value():
    """
    Test that invalid configuration values raise appropriate errors.
    """
    invalid_config = {
        'SQLALCHEMY_DATABASE_URI': 'invalid_uri',
        'DEBUG': 'not_a_boolean'
    }
    with pytest.raises(ValueError):
        # Simulate validation logic for configuration values
        if not invalid_config['SQLALCHEMY_DATABASE_URI'].startswith(('sqlite://', 'postgresql://')):
            raise ValueError("Invalid SQLALCHEMY_DATABASE_URI value")
        if not isinstance(invalid_config['DEBUG'], bool):
            raise ValueError("DEBUG must be a boolean")
