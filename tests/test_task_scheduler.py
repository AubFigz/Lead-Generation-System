from task_scheduler import execute_script, schedule_tasks
import subprocess
import pytest
from unittest.mock import patch, MagicMock
import schedule


@patch("subprocess.run")
def test_execute_script_success(mock_subprocess_run):
    """
    Test successful script execution with subprocess.
    """
    mock_subprocess_run.return_value.returncode = 0
    mock_subprocess_run.return_value.stdout = "Success"
    mock_subprocess_run.return_value.stderr = ""

    execute_script("test_script.py", {})

    # Assertions
    mock_subprocess_run.assert_called_once_with(
        ["python", "test_script.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    assert mock_subprocess_run.return_value.returncode == 0, "Script should execute successfully"


@patch("subprocess.run")
def test_execute_script_failure(mock_subprocess_run):
    """
    Test script execution failure and error handling.
    """
    mock_subprocess_run.return_value.returncode = 1
    mock_subprocess_run.return_value.stderr = "Error occurred"

    with pytest.raises(Exception, match="Exception while executing test_script.py"):
        execute_script("test_script.py", {})

    # Assertions
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.return_value.returncode == 1, "Script should fail with return code 1"


@patch("schedule.every")
def test_schedule_tasks_day_interval(mock_schedule):
    """
    Test scheduling of daily tasks.
    """
    config = {
        'task_scheduler': {
            'tasks': [
                {'script': 'test_script.py', 'time': '00:00', 'interval': 'day'}
            ]
        }
    }
    schedule_tasks(config)

    # Assertions
    mock_schedule().day.at.assert_called_once_with("00:00")
    assert mock_schedule().day.at.called, "Task should be scheduled at 00:00"


@patch("schedule.every")
def test_schedule_tasks_minute_interval(mock_schedule):
    """
    Test scheduling of minute-interval tasks.
    """
    config = {
        'task_scheduler': {
            'tasks': [
                {'script': 'test_script.py', 'interval': 'minute'}
            ]
        }
    }
    schedule_tasks(config)

    # Assertions
    mock_schedule().minute.do.assert_called_once()
    assert mock_schedule().minute.do.called, "Task should be scheduled every minute"


@patch("schedule.every")
def test_schedule_tasks_hour_interval(mock_schedule):
    """
    Test scheduling of hourly tasks.
    """
    config = {
        'task_scheduler': {
            'tasks': [
                {'script': 'test_script.py', 'interval': 'hour'}
            ]
        }
    }
    schedule_tasks(config)

    # Assertions
    mock_schedule().hour.do.assert_called_once()
    assert mock_schedule().hour.do.called, "Task should be scheduled every hour"


def test_schedule_tasks_invalid_interval(mocker):
    """
    Test behavior for invalid task intervals.
    """
    mock_logger = mocker.patch("logging.error")
    config = {
        'task_scheduler': {
            'tasks': [
                {'script': 'test_script.py', 'interval': 'unknown'}
            ]
        }
    }
    schedule_tasks(config)

    # Assertions
    mock_logger.assert_called_once_with("Unknown interval unknown for script test_script.py.")

