from app import db
from app import Lead

def seed_data():
    leads = [
        Lead(name="John Doe", email="john@example.com", phone="1234567890", score=0.9, status="New"),
        Lead(name="Jane Smith", email="jane@example.com", phone="0987654321", score=0.8, status="Contacted"),
    ]
    db.session.bulk_save_objects(leads)
    db.session.commit()
    print("Database seeded with test data.")

if __name__ == "__main__":
    seed_data()
