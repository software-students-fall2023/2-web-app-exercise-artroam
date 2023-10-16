from flask import Flask, render_template, request, redirect, url_for, session
from flask_session.__init__ import Session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from os.path import join, dirname
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

sess = Session()
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

sess.init_app(app)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Create a new client and connect to the server
client = MongoClient(os.environ.get('MONGO_URI'), server_api=ServerApi('1'))
#client = MongoClient("mongodb+srv://artroam_user:artroam123@artroam-cluster.fezhsez.mongodb.net/?retryWrites=true&w=majority", server_api=ServerApi('1'))

# turn on debugging if in development mode
if os.environ.get('FLASK_ENV', 'development') == 'development':
    app.debug = True # debug mode

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping') 
    db = client[os.environ.get('MONGO_DBNAME')]
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print('Database connection error', e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

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