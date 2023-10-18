from flask import Flask, url_for, redirect, render_template, make_response, session, request,  jsonify, abort
from flask_session import Session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
# from utils.helpers import upload_file_to_s3
import os
from bson.objectid import ObjectId   
import boto3
import uuid
import datetime

# Initializes the flask application and loads the .env file to retreive information from the MongoDB Atlas Database
app = Flask(__name__)
load_dotenv()

# This is to monitor Flask's session management. Flask uses a secret key to sign and encrypt session data to prevent tampering and ensure security. 
# This secret key is essential for the proper functioning of user sessions in your Flask application.
# This is essentially when users sign into their account, it simply creates a private session for them (for security and privacy reasons)
sess = Session()
app.secret_key = os.getenv('APP_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
sess.init_app(app)

# AWS S3 Bucket Configuration 
s3 = boto3.client('s3', region_name='us-east-1', 
                  aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), 
                  aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY'))

# Checks that if the FLASK_ENV is in development, we switch on debugging
if os.getenv('FLASK_ENV', 'development') =='development':
    app.debug = True

# Establish a database connection with the MONGO_URI (MongoDB Atlas connection)
client = MongoClient(os.getenv('MONGO_URI'))
database = client[os.getenv('MONGO_DBNAME')]

# Checks if the connection has been made, else make an error printout
try:
    client.admin.command('ping')                
    database = database[os.getenv('MONGO_DBNAME')]      
    print('* Connected to MongoDB!')         

except Exception as err:
    print('* "Failed to connect to MongoDB at', os.getenv('MONGO_URI'))
    print('Database connection error:', err) 

# Helper func
def generate_unique_filename(original_filename):
    extension = original_filename.split('.')[-1]
    unique_filename = "{}-{}.{}".format(datetime.datetime.now().strftime('%Y%m%d%H%M%S'), uuid.uuid4(), extension)
    
    return unique_filename

# Routes: 
# Default home route which will be the explore page         
@app.route('/')
def home(): 
    artworks = database.posts.find({}).sort("created_at", -1)
    return render_template('index.html', artworks = artworks)

 # Route to upload a photo or take a photo 
@app.route('/create', methods=['POST', 'GET'])
def create():
    session['image_on_post_page'] = False
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()

            if 'image' in data:
                import base64
                image_data = base64.b64decode(data['image'].split(",")[-1])
                file_name = generate_unique_filename("image.jpg")
                s3.put_object(Bucket=os.getenv('BUCKET_NAME'), Key=file_name, Body=image_data, ContentType='image/jpeg')
                
                session['uploaded_file_key'] = file_name
                session['image_viewed'] = False 
                session['image_on_post_page'] = False

                redirect_url = url_for('post')
                return jsonify({'redirect': redirect_url})

    return render_template('create.html')

@app.route('/gallery', methods = ['GET'])
def gallery():
    return render_template('gallery.html')

# @app.route('/gallery/save', methods = ['POST'])
# def gallery_save():
#     # check whether an input field with name 'image_uploads' exist
#     if 'image_uploads' not in request.files:
#         flash('No image_uploads key in request.files')
#         return redirect(url_for('gallery'))

#     # after confirm 'image_uploads' exist, get the file from input
#     file = request.files['image_uploads']

#     # check whether a file is selected
#     if file.filename == '':
#         flash('No selected file')
#         return redirect(url_for('gallery'))

#     # check whether the file extension is allowed (eg. png,jpeg,jpg,gif)
#     if file:
#         output = upload_file_to_s3(file) 
        
#         # if upload success,will return file name of uploaded file
#         if output: 
#             # TODO: save the file name in database

#             flash("Success upload: {}".format(output))
#             return redirect(url_for('gallery'))

#         # upload failed, redirect to upload page
#         else:
#             flash("Unable to upload, try again")
#             return redirect(url_for('gallery'))
        
#     # if file extension not allowed
#     else:
#         flash("File type not accepted,please try again.")
#         return redirect(url_for('gallery'))

# Route to make a post
@app.route('/post', methods=['POST', 'GET'])
def post():
    try:
        session['image_on_post_page'] = True
        if 'uploaded_file_key' not in session:
            abort(400, description="Image not found in session")

        image_url = f"https://{os.getenv('BUCKET_NAME')}.s3.amazonaws.com/{session['uploaded_file_key']}"

        session['image_viewed'] = True
        return render_template('post.html', image_url=image_url)

    except Exception as e:
        print(f"An error occurred: {e}")
        abort(500, description="Internal server error")
        
# Route to upload posts
@app.route('/post_data', methods=['POST'])
def post_data():
    posts_collection = database['posts']
    try:
        username = session.get('username')
        user_id = session.get('user_id')
        post_description = request.form.get('post_description')
        image_url = session.get('uploaded_file_key', None)
        if image_url:
            image_url = f"https://{os.getenv('BUCKET_NAME')}.s3.amazonaws.com/{image_url}"
        post = {
            "user_id": user_id, 
            "username": username,
            "likes": 0,
            "post_description": post_description,
            "image_url": image_url,
            "created_at": datetime.datetime.utcnow()  
        }

        posts_collection.insert_one(post)
        return redirect(url_for('home'))
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to submit post", 500

@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', message=e.description), 400

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', message=e.description), 500

# Route to delete image
@app.route('/delete_image', methods=['POST'])
def delete_image():
    s3.delete_object(Bucket=os.getenv('BUCKET_NAME'), Key=session['uploaded_file_key'])
    del session['uploaded_file_key']  
    session['image_on_post_page'] = False
    return redirect(url_for('create')) 

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
            session['username'] = username

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
