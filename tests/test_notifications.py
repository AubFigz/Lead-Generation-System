from notifications import notify_stakeholders, export_to_csv
import pandas as pd
import os
import pytest
from unittest.mock import patch, MagicMock


def test_export_to_csv(tmp_path):
    """
    Test exporting leads to a CSV file.
    """
    leads = pd.DataFrame({'Name': ['Project A', 'Project B'], 'Score': [0.85, 0.90]})
    file_name = "leads.csv"
    file_path = tmp_path / file_name

    # Export to CSV
    export_to_csv(leads, file_name, {'export': {'directory': tmp_path}})

    # Assertions
    assert os.path.exists(file_path), "Exported CSV file not found"
    exported_data = pd.read_csv(file_path)
    assert exported_data.shape == leads.shape, "Exported CSV does not match the input DataFrame"
    assert all(exported_data['Name'] == leads['Name']), "Data mismatch in 'Name' column"
    assert all(exported_data['Score'] == leads['Score']), "Data mismatch in 'Score' column"


def test_export_to_csv_invalid_directory():
    """
    Test exporting leads to an invalid directory.
    """
    leads = pd.DataFrame({'Name': ['Project A', 'Project B'], 'Score': [0.85, 0.90]})
    invalid_dir = "/invalid_directory/leads.csv"

    with pytest.raises(Exception):
        export_to_csv(leads, invalid_dir, {})


@patch("smtplib.SMTP_SSL")
def test_notify_stakeholders_success(mock_smtp):
    """
    Test successful email notifications.
    """
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    notify_stakeholders(
        ['recipient@example.com'],
        "Test Subject",
        "Test Message",
        {
            'notifications': {
                'enabled': True,
                'smtp_server': "smtp.example.com",
                'port': 465,
                'sender_email': "sender@example.com",
                'email_auth': {
                    'password': "password"
                }
            }
        }
    )

    # Assertions
    mock_smtp.assert_called_once_with("smtp.example.com", 465)
    mock_server.login.assert_called_once_with("sender@example.com", "password")
    mock_server.sendmail.assert_called_once()
    assert mock_server.sendmail.call_args[0][0] == "sender@example.com"
    assert "recipient@example.com" in mock_server.sendmail.call_args[0][1]


@patch("smtplib.SMTP_SSL")
def test_notify_stakeholders_disabled(mock_smtp):
    """
    Test email notifications when disabled in the configuration.
    """
    notify_stakeholders(
        ['recipient@example.com'],
        "Test Subject",
        "Test Message",
        {
            'notifications': {
                'enabled': False
            }
        }
    )

    # Assert that SMTP is not called
    mock_smtp.assert_not_called()


@patch("smtplib.SMTP_SSL")
def test_notify_stakeholders_failure(mock_smtp):
    """
    Test email notification failure and retry mechanism.
    """
    mock_smtp.side_effect = Exception("SMTP Connection Error")

    with pytest.raises(Exception):
        notify_stakeholders(
            ['recipient@example.com'],
            "Test Subject",
            "Test Message",
            {
                'notifications': {
                    'enabled': True,
                    'smtp_server': "smtp.example.com",
                    'port': 465,
                    'sender_email': "sender@example.com",
                    'email_auth': {
                        'password': "password"
                    }
                },
                'system': {
                    'max_retries': 3,
                    'retry_backoff': 1
                }
            }
        )

    # Assert retry attempts
    assert mock_smtp.call_count == 3, "Retry attempts did not match the configured limit"
