from flask import Flask, render_template, request, redirect, url_for, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Create a new client and connect to the server
client = MongoClient(os.getenv('MONGO_URI'), server_api=ServerApi('1'))

# Turn on debugging if in development mode
if os.getenv('FLASK_ENV', 'development') == 'development':
    app.debug = True 

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

@app.route('/gallery', methods = ['GET','POST'])
def gallery():
    if request.method == 'POST':
        images = request.form['image_uploads']
        response = make_response(images, 200)
        response.mimetype = "text/plain"
        return response
    else:
        return render_template('gallery.html')

@app.route('/profile')
def profile():
    if 'user_id' in session:
        return render_template('profile.html') 
    else:
        return "Please log in first!"
    
    #feel free to change / edit, just a placeholder to ensure we don't forget!
    

@app.route('/signup', methods = ['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if db.users.find_one({'username': username}):
            uname_error = "Username already exists!"
            return render_template('signup.html', uname_error = uname_error)
        
        elif db.users.find_one({'email': email}):
            email_error = "Email already used, try another or try logging in!"
            return render_template('signup.html', email_error = email_error)
        
        elif len(password) < 8 & len(password) > 20:
            passlen_error = "Password must be between 8 and 20 characters long!"
            return render_template('signup.html', passlen_error = passlen_error)
        
        elif not any(char.isdigit() for char in password):
            passnum_error = "Password should have at least one number!"
            return render_template('signup.html', passnum_error = passnum_error)
        
        elif not any(char.isalpha() for char in password):
            passalph_error = "Password should have at least one alphabet!"
            return render_template('signup.html', passalph_error = passalph_error)
        
        password_hash = generate_password_hash(password)

        db.users.insert({
            'username': username,
            'password': password_hash,
            'email': email
        })

    return redirect(url_for('profile'))

@app.route('/login', methods = ['GET','POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    user = db.users.find_one({'username': username})

    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        return redirect(url_for('profile'))

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)