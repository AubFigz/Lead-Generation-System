from notifications import notify_stakeholders

if __name__ == "__main__":
    subject = "Weekly Leads Report"
    message = "This is your weekly update on leads."
    notify_stakeholders(["manager@example.com"], subject, message, {})
