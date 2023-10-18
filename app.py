from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session.__init__ import Session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from utils.helpers import upload_file_to_s3
import os
from os.path import join, dirname

app = Flask(__name__)

sess = Session()
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

sess.init_app(app)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = 'some secret'
load_dotenv()

# Create a new client and connect to the server
client = MongoClient(os.environ.get('MONGO_URI'), server_api=ServerApi('1'))
#client = MongoClient("mongodb+srv://artroam_user:artroam123@artroam-cluster.fezhsez.mongodb.net/?retryWrites=true&w=majority", server_api=ServerApi('1'))

# turn on debugging if in development mode
if os.environ.get('FLASK_ENV', 'development') == 'development':
    app.debug = True # debug mode

# Send a ping to confirm a successful connection else, print out the error
try:
    client.admin.command('ping')
    db = client[os.getenv('MONGO_DBNAME')]
    print("* Successfully connected to MongoDB!")
except Exception as err:
    print('Failed to connect to MongoDB at, ', os.getenv('MONGO_URI'))
    print('Database error: ', err)

# Routes: 
@app.route('/')
def index():
    # artworks = db.artposts.find({}).sort("created_at", -1)
    return render_template('index.html')

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/gallery', methods = ['GET'])
def gallery():
    return render_template('gallery.html')

@app.route('/gallery/save', methods = ['POST'])
def gallery_save():
    # check whether an input field with name 'image_uploads' exist
    if 'image_uploads' not in request.files:
        flash('No image_uploads key in request.files')
        return redirect(url_for('gallery'))

    # after confirm 'image_uploads' exist, get the file from input
    file = request.files['image_uploads']

    # check whether a file is selected
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('gallery'))

    # check whether the file extension is allowed (eg. png,jpeg,jpg,gif)
    if file:
        output = upload_file_to_s3(file) 
        
        # if upload success,will return file name of uploaded file
        if output: 
            # TODO: save the file name in database

            flash("Success upload: {}".format(output))
            return redirect(url_for('gallery'))

        # upload failed, redirect to upload page
        else:
            flash("Unable to upload, try again")
            return redirect(url_for('gallery'))
        
    # if file extension not allowed
    else:
        flash("File type not accepted,please try again.")
        return redirect(url_for('gallery'))

@app.route('/profile')
def profile():
    if 'user_id' in session:
        return render_template('profile.html') 
    else:
        return render_template('login.html')
    
    #feel free to change / edit, just a placeholder to ensure we don't forget!

#backend code for signup page
@app.route('/signup', methods = ['GET','POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            email = request.form['email']
            print(username, password, confirm_password, email)

            errors = []
                
            if db.users.find_one({'username': username}):
                errors.append("Username already exists!")
            
            if db.users.find_one({'email': email}):
                errors.append("Email already used, try another or try logging in!")
            
            if len(password) < 8 & len(password) > 20:
                errors.append("Password must be between 8 and 20 characters long!")
            
            if not any(char.isdigit() for char in password):
                errors.append("Password should have at least one number!")
            
            if not any(char.isalpha() for char in password):
                errors.append("Password should have at least one alphabet!")
            
            if not confirm_password == password:
                errors.append("Passwords do not match!")

            if errors:
                return render_template('signup.html', errors=errors)
            
            else:
                password_hash = generate_password_hash(password)

                db.users.insert_one({
                    'username': username,
                    'password': password_hash,
                    'email': email
                })

                return redirect(url_for('login'))

        return render_template('signup.html')

@app.route('/login', methods = ['GET'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    else:
        return render_template('login.html')

@app.route('/login_auth', methods = ['GET','POST'])
def login_auth():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            errors = []
            
            user = db.users.find_one({'username': username})

            if user and check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                return redirect(url_for('index'))
            
            else:
                errors.append("Invalid username or password!")
                return render_template('login.html', errors=errors)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)