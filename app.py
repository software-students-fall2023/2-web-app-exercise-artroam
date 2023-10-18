from flask import Flask, url_for, redirect, render_template, make_response, session, request
from flask_session import Session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId   

# Initializes the flask application and loads the .env file to retreive information from the MongoDB Atlas Database
app = Flask(__name__)
load_dotenv()

# This is to monitor Flask's session management. Flask uses a secret key to sign and encrypt session data to prevent tampering and ensure security. 
# This secret key is essential for the proper functioning of user sessions in your Flask application.
# This is essentially when users sign into their account, it simply creates a private session for them (for security and privacy reasons)
sess = Session()
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
sess.init_app(app)

# Checks that if the FLASK_ENV is in development, we switch on debugging
if os.getenv('FLASK_ENV', 'development') =='development':
    app.debug = True

# Establish a database connection with the MONGO_URI (MongoDB Atlas connection)
db_cxn = MongoClient(os.getenv('MONGO_URI'))

# Checks if the connection has been made, else make an error printout
try:
    db_cxn.admin.command('ping')                
    database = db_cxn[os.getenv('MONGO_DBNAME')]      
    print('* Connected to MongoDB!')         

except Exception as err:
    print('* "Failed to connect to MongoDB at', os.getenv('MONGO_URI'))
    print('Database connection error:', err) 

# Routes: 
# Default home route which will be the explore page
@app.route('/')
def home(): 
    artworks = database.artposts.find({}).sort("created_at", -1)
    return render_template('index.html', artworks=artworks)

# Create Page: Users can post artworks
@app.route('/create')
def create(): 
    return render_template('create.html')

# Gallery Page: Users can see their saved artworks
@app.route('/gallery')
def gallery(): 
    return render_template('gallery.html')

# Users can view their profile
@app.route('/profile')
def profile(): 
    # This checks that if the user in the session has an ID (meaning they have an account in the webapp, then they can access their profile page)
    if 'user_id' in session: 
        user_id = ObjectId(session['user_id'])
        user = database.users.find_one({'_id': user_id})
        return render_template('profile.html', user=user)
    # Else, if they don't have an account, it will redirect them to the login page
    else: 
        return render_template('login.html')

# This is the function which registers the signup page from the login.html page if the user does click it
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If there is a user_id in session, it redirects them back to the home page
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    # If there is no account, then we allow the user to creat one. 
    else: 
        if request.method == 'POST':

            # We allow the user to create their username, password, confirm password, email
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            email = request.form['email']

            # Debugging console test
            print(username, password, confirm_password, email)

            errors = []
            
            # This checks if there is already a user that has this exact username
            if database.users.find_one({'username': username}):
                errors.append("Username already exists!")
            
            # This checks if there is already a user that has this exact email
            if database.users.find_one({'email': email}):
                errors.append("Email already used, try another or try logging in!")
            
            # This checks if the password is in between 8-20 characters
            if len(password) < 8 & len(password) > 20:
                errors.append("Password must be between 8 and 20 characters long!")
            
            # This checks if the password does not have any numbers
            if not any(char.isdigit() for char in password):
                errors.append("Password should have at least one number!")
            
            # This checks if the password does not have any alphabets
            if not any(char.isalpha() for char in password):
                errors.append("Password should have at least one alphabet!")
            
            # This checks if the password and the confirm password do not match
            if not confirm_password == password:
                errors.append("Passwords do not match!")

            # If there are any errors, it will re-render the signup.html page and allow the user to try again
            if errors:
                return render_template('signup.html', errors=errors)
            
            # If the user managed to create a proper account, it will generate a hash for their password 
            else:
                password_hash = generate_password_hash(password)

            # Here we insert their account details to the database
            database.users.insert_one({
                'username': username,
                'password': password_hash,
                'email': email
            })

            # Once that's done, it will redirect the user to the login page where they must login to access the webpage. 
            return redirect(url_for('login'))
        
        # Renders the signup.html page
        return render_template('signup.html')


# This function is for rendering either the login.html template if they haven't logged in and if they have, then we render the home page
@app.route('/login', methods=['GET'])
def login(): 
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    else:
        return render_template('login.html')

# This function is the backend of the login functionality from the login.html file
@app.route('/login_auth', methods=['POST'])
def login_auth(): 
    # If a user is already logged in, redirect them to the home page
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    # Else, ask them to login by inputting a username and password
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            errors = []
            
            # Once they've inputted their username and password, we search the database if there is someone already with this username
            user = database.users.find_one({'username': username})

            # If we have a user and the password they gave matches with the hash function, we provide the _id attribute of the user to the user_id in the session
            if user and check_password_hash(user['password'], password):    
                # This is how keep keep track of which user is currently authenticated or logged in. We store the user_id string into the user's session
                session['user_id'] = str(user['_id'])
                return redirect(url_for('home'))
            
            # If the username or password does not match, that means either one is wrong, hence we render the login.html template so they can attempt once more.
            else:
                errors.append("Invalid username or password!")
                return render_template('login.html', errors=errors)

# Here we have another route, if the user decides to logout, it will pop their user_id from the session and redirect them to the login page
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# This is a route to handle any errors that may occur during any HTTP requests
@app.errorhandler(Exception)
def handle_error(err):
    return render_template('error.html', error=err)

# Executing the Flask Application: 
if(__name__ == "__main__"):
    app.run(debug=True)
