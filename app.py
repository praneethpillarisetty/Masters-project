from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Add a secret key for Flask-Login
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Define User model with Flask-Login's UserMixin
class User(UserMixin, db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    public_key = db.Column(db.String(2000), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        public_key = request.form['public_key']

        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(existing_user)
            return "Email already exists. Please choose a different email."

        # Create a new user object
        new_user = User(first_name=first_name, last_name=last_name, email=email, password=password, public_key=public_key)

        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        return "User registered successfully!"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        publickey = request.form['public_key']
        user = User.query.filter_by(email=email).first()

        if user and user.password == password and publickey == user.public_key:
            # Login user and store public key
            login_user(user)
            user_data = {'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email, 'public_key': user.public_key}
            return redirect(url_for('home', user_data=user_data))
        else:
            return "Invalid email or password."
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    user_data = {'first_name': current_user.first_name, 'last_name': current_user.last_name, 'email': current_user.email, 'public_key': current_user.public_key}
    return render_template('home.html', user_data=user_data)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.config['UPLOAD_FOLDER'] = 'static/temp'
    app.run(debug=True)
