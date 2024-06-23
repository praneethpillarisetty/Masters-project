from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
import os

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

class MetaData(db.Model):
    __tablename__ = "Meta_Data"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    description = db.Column(db.String(500))
    tags = db.Column(db.String(500))  # Store tags as a comma-separated string
    data_type = db.Column(db.String(50))
    hash_id = db.Column(db.String(500), unique=True)
    digital_signature = db.Column(db.String(500))
    encryption_key = db.Column(db.String(500))
    internal_url = db.Column(db.String(500))
    external_url = db.Column(db.String(500))
    shared_type = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_email', methods=['POST'])
def check_email():
    email = request.json.get('email')
    print(f"Checking email: {email}")
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print('User exists')
        return jsonify({'exists': True})
    print('User does not exist')
    return jsonify({'exists': False})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        encrypted_public_key = request.form['public_key']
        
        new_user = User(first_name=first_name, last_name=last_name, email=email, password=password, public_key=encrypted_public_key)
        
        db.session.add(new_user)
        db.session.commit()
        print('user is added')
        return jsonify({'success': True})
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        public_key = request.form['public_key']
        user = User.query.filter_by(email=email).first()
        key_file_location = request.form['file_name'] 
        print(public_key,'\n',user.public_key)
        if user and user.password == password and public_key == user.public_key:
            # Login user and store public key
            login_user(user)
            session['key_file_path'] = key_file_location
            user_data = {'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email, 'public_key': user.public_key}
            return redirect(url_for('home', user_data=user_data))
        else:
            return "Invalid email or password."
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('key_file_location', None)
    logout_user()
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    user_data = {'first_name': current_user.first_name, 'last_name': current_user.last_name, 'email': current_user.email, 'public_key': current_user.public_key}
    return render_template('home.html', user_data=user_data)


@app.route('/search_history')
@login_required
def search_history():
    return render_template('search_history.html')

@app.route("/upload", methods=["GET", "POST"])
@login_required
def user_upload():
    if request.method == "POST":
        file = request.files['file']
        description = request.form['description']
        tags = request.form['tags']
        data_type = request.form['data_type']
        digital_signature = request.form['digital_signature']
        encrypted_key = request.form['encrypted_key']
        
        tags_list = [tag.strip() for tag in tags.split(',')]

        # Create a directory named after the user's email if it doesn't exist
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.email)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # Save the file to the user's directory
        file_path = os.path.join(user_folder, file.filename)
        file.save(file_path)

        user_data = MetaData(
            user_id=current_user.id,
            description=description,
            tags=','.join(tags_list),
            data_type=data_type,
            digital_signature=digital_signature,
            encryption_key=encrypted_key,
            internal_url=file_path,
            external_url = '',
            shared_type = 'Private'
        )

        db.session.add(user_data)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("upload.html")

@app.route('/view_post')
@login_required
def view_post():
    user_id = current_user.id
    metadata_list = MetaData.query.filter_by(user_id=user_id).all()
    return render_template('view_post.html', metadata_list=metadata_list)

@app.route('/get_file_data/<int:post_id>', methods=['GET'])
@login_required
def get_file_data(post_id):
    metadata = MetaData.query.get(post_id)
    if metadata and metadata.user_id == current_user.id:
        with open(metadata.internal_url, 'rb') as file:
            encrypted_file_data = file.read()
        response = {
            'description': metadata.description,
            'tags': metadata.tags,
            'data_type': metadata.data_type,
            'hash_id': metadata.hash_id,
            'digital_signature': metadata.digital_signature,
            'encryption_key': metadata.encryption_key,
            'encrypted_file_data': encrypted_file_data.hex()
        }
        return jsonify(response)
    return jsonify({'error': 'Post not found or access denied'}), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.config['UPLOAD_FOLDER'] = 'static/temp'
    app.run(debug=True)
