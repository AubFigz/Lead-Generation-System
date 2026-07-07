import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")
audit_handler = logging.FileHandler("audit.log")
audit_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

def log_action(user, action, details):
    """
    Logs user actions for auditing.
    Args:
        user (str): Username performing the action.
        action (str): Action performed.
        details (str): Additional details about the action.
    """
    audit_logger.info(f"User: {user}, Action: {action}, Details: {details}")

# Example usage
if __name__ == "__main__":
    log_action("admin", "Update Lead", "Updated lead with ID 123")
