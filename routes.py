from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session
from bson.objectid import ObjectId
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import sqlite3

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a strong secret key in production

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")  # Update if using a different host or port
mongo_db = mongo_client["safehaven"]  # Replace 'safehaven' with your desired database name

# Blueprint setup
routes = Blueprint('routes', __name__)

# ---------------------------------
# General Routes
# ---------------------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    patients = mongo_db.patients.find()  # Fetch patients from MongoDB
    return render_template('dashboard.html', patients=patients)

# ---------------------------------
# User Authentication Routes
# ---------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("All fields are required.", "error")
            return redirect(url_for('register_user'))

        hashed_password = generate_password_hash(password)

        try:
            mongo_db.users.insert_one({'username': username, 'password': hashed_password})
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('login_user'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "error")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = mongo_db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Please try again.", "error")
    
    return render_template('login.html')

@app.route('/logout')
def logout_user():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login_user'))

# ---------------------------------
# Patient Management Routes
# ---------------------------------

@routes.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patient_data = {
            'name': request.form['patient_name'],
            'age': request.form['age'],
            'condition': request.form['condition']
        }
        mongo_db.patients.insert_one(patient_data)
        flash('Patient added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_patient.html')

@routes.route('/delete_patient/<id>', methods=['POST'])
@login_required
def delete_patient(id):
    mongo_db.patients.delete_one({'_id': ObjectId(id)})
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@routes.route('/update_patient/<id>', methods=['GET', 'POST'])
@login_required
def update_patient(id):
    patient = mongo_db.patients.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        updated_data = {
            'name': request.form['name'],
            'age': request.form['age'],
            'condition': request.form['condition']
        }
        mongo_db.patients.update_one({'_id': ObjectId(id)}, {'$set': updated_data})
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('update_patient.html', patient=patient)

# ---------------------------------
# SQLite Functions (Optional)
# ---------------------------------

def get_patient_by_id(patient_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'age': row[2],
            'gender': row[3],
            'stroke': row[4]
        }
    return None

def delete_patient_by_id(patient_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    affected_rows = cursor.rowcount
    conn.close()
    return affected_rows > 0

# ---------------------------------
# Register Blueprint and Run App
# ---------------------------------

app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)
