from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # DO NOT USE IN PRODUCTION 
# app.secret_key = secrets.token_hex(16)  # Use this in production for a secure random key

# Configure SQLAlchemy with SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database configuration
class User(db.Model):
    # class variables
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # methods for password hashing and checking
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password): 
        return check_password_hash(self.password, password)

# Routes, starting with 'home' route
@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

# Login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    # Collect information from the form in index.html
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        # Check if user already exists in the database 
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
    else:
        return render_template("index.html", error="Invalid login credentials. Please try again.")



# Registration route
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if user already exists in the database
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template("index.html", error="Username already exists. Please choose a different username.")
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if "username" in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('home'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)