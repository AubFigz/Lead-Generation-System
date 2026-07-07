from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate
from flasgger import Swagger
from pydantic import BaseModel, EmailStr, ValidationError
from flask_cors import CORS
from auth import hash_password, verify_password
from config import configurations

# Initialize app and load configuration
app = Flask(__name__)
CORS(app)  # Enable CORS
config_type = "development"  # Change to "production" as needed
app.config.from_object(configurations[config_type])
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Unauthorized"}), 401
swagger = Swagger(app)

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(self.password_hash, password)

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    score = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="New")

# Pydantic Schema
class LeadSchema(BaseModel):
    name: str
    email: EmailStr
    phone: str
    score: float
    status: str

# Login Manager Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "User already exists"}), 400
        user = User(username=data['username'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            login_user(user)
            return jsonify({"message": "Login successful"}), 200
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    leads = Lead.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify([{
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'phone': lead.phone,
        'score': lead.score,
        'status': lead.status
    } for lead in leads.items])

@app.route('/api/leads', methods=['POST'])
@login_required
def create_lead():
    try:
        lead_data = LeadSchema(**request.json)
        lead = Lead(**lead_data.model_dump())
        db.session.add(lead)
        db.session.commit()
        return jsonify({"message": "Lead created successfully"}), 201
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['PUT'])
@login_required
def update_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    try:
        lead_data = LeadSchema(**request.json)
        for key, value in lead_data.model_dump().items():
            setattr(lead, key, value)
        db.session.commit()
        return jsonify({"message": "Lead updated successfully"}), 200
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
@login_required
def delete_lead(lead_id):
    try:
        lead = Lead.query.get_or_404(lead_id)
        db.session.delete(lead)
        db.session.commit()
        return jsonify({"message": "Lead deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)

