import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import app, db

@pytest.fixture(scope='module')
def test_client():
    """
    Provides a Flask test client for the app, with an in-memory SQLite database.
    Ensures the database is created and destroyed appropriately for tests.
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite database
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create all tables
        yield client
        with app.app_context():
            db.session.remove()  # Clean up the session
            db.drop_all()  # Drop all tables

@pytest.fixture(scope='function')
def db_session():
    """
    Provides a SQLAlchemy session for database testing.
    This uses an in-memory SQLite database for isolated testing.
    """
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()  # Clean up the session
    engine.dispose()  # Dispose of the engine

