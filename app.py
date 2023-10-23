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
from utils import get_user_by_id, get_favorites_by_ids, unlike_post_by_id
from urllib.parse import urlparse

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

# Checks if the connection has been made, else make an error printout
try:
    client.admin.command('ping')          
    database = client[os.getenv('MONGO_DBNAME')]          
    print('* Connected to MongoDB!')         

except Exception as err:
    print('* "Failed to connect to MongoDB at', os.getenv('MONGO_URI'))
    print('Database connection error:', err) 

# Helper function for creatte() to generate unique filename for uploads
def generate_unique_filename(original_filename):
    extension = original_filename.split('.')[-1] # Extracts the file extension
    unique_filename = "{}-{}.{}".format(datetime.datetime.now().strftime('%Y%m%d%H%M%S'), uuid.uuid4(), extension) # The filename consists of the "timestamp_randomUUID.file extension)
    return unique_filename

# Routes: 
# Default home route which will be the explore page         
@app.route('/')
def home(): 
    artworks = list(database.posts.find({}).sort("created_at", -1))
    
    for artwork in artworks:
        user_id = artwork.get('user_id', None)
        if user_id:
            try:
                user_object_id = ObjectId(user_id)
                user = database.users.find_one({'_id': user_object_id})
                if user:
                    artwork['avatar_url'] = user.get('avatar_url', None) 
                    print(f"User ID: {user_id} -> Avatar URL: {artwork['avatar_url']}")
                else:
                    print(f"No user found for User ID: {user_id}")
            except Exception as e:
                print(f"Error converting user_id {user_id} to ObjectId: {e}")
        else:
            print("No user_id field in this artwork.")
    
    return render_template('index.html', artworks=artworks)


# This route is for the search bar and it finds the posts that have the same title as the user searched for.
@app.route('/search', methods=['GET'])
def search_posts():
    search_query = request.args.get('search')
    
    # If the search query is a non-character value, we return nothing.
    if not search_query:
        print("TEST1")
        no_posts_found = True
        artworks = []

    else:
        artworks = list(database.posts.find({'post_title': {'$regex': search_query, '$options': 'i'}}).sort("created_at", -1))
        no_posts_found = len(artworks)==0  

    return render_template('index.html', artworks=artworks, no_posts_found=no_posts_found)

# This route is for the filter menu and it only retrieves artworks which have a certain tag.
@app.route('/filter/<tag>', methods=['GET'])
def filter_posts(tag):
    artworks = list(database.posts.find({'art_type': tag}).sort("created_at", -1))
    no_posts_found = len(artworks)==0  
    return render_template('index.html', artworks=artworks, no_posts_found=no_posts_found)

# This route will allow the user to like a specific post in real time. 
@app.route('/like_post/<post_id>', methods=['POST'])
def like_post(post_id):
    try:
        # Correctly formatting the post_id
        post_id = ObjectId(post_id)

        # Finding the post from the database and the user_id (in session)
        post = database.posts.find_one({'_id': post_id})
        user_id = session.get('user_id')

        # If the user is logged in they can like the posts, otherwise, it will redirect them to the login page. 
        if user_id:
            # If the post is a valid post in the database it checks 
            if post:
                # Retrieve the array of users who liked the post from the database
                users_that_like_post = post.get('users_that_like_post', [])

                # If the user is not in the array of users that likes the post, this means they like the post and therefore are added to the array
                # Likewise, if the user is in the array of users that likes the post, this means they want to unlike the post and are thus removed from this array
                if user_id in users_that_like_post:
                    users_that_like_post.remove(user_id)
                    liked = False
                else:
                    users_that_like_post.append(user_id)
                    liked = True

                # Update the database
                database.posts.update_one({'_id': post_id}, {'$set': {'likes': len(users_that_like_post), 'users_that_like_post': users_that_like_post}})

                # Return the updated like count based on the number of people in the user_that_likes_post array
                return jsonify({'likes': len(users_that_like_post), 'liked': liked})

            else:
                print("Not Liking")
                return jsonify({'error': 'Post not found'}, 404)
        
        elif user_id == None:
            return jsonify({'redirect': url_for('login')})
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to like post", 500


# This is a route for the explore page for the user to save posts into their favorites array which will therefore save the post to the gallery
@app.route('/save_post/<post_id>', methods=['POST'])
def save_post(post_id):
    try:
        # Check if the user is logged in
        user_id = session.get('user_id')
        if user_id:
            # Get the current user and their favoritees array
            current_user = get_user_by_id(user_id)
            favorites = current_user.get('favorites', [])
            
            # Check if the post is already in the user's favorites
            if post_id in favorites:
                favorites.remove(ObjectId(post_id))  # Remove the post from favorites
                saved = False
            else:
                favorites.insert(0, ObjectId(post_id))  # Add the post to favorites
                print(favorites)
                saved = True
            
            # Update the user's favorites array in the database
            database.users.update_one({'_id': current_user['_id']}, {'$set': {'favorites': favorites}})
            
            # Return a JSON response to indicate the post has been saved or removed
            return jsonify({'favorites': list(map(lambda x: str(x), favorites)), 'saved': saved})
        
        elif user_id == None:
            return jsonify({'redirect': url_for('login')})

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to save post", 500


# This route is loaded at the very beginning when the web page is loaded to remember which posts the user saved
@app.route('/get_saved_posts', methods=['GET'])
def get_saved_posts():
    user_id = session.get('user_id')
    
    if user_id:
        user = get_user_by_id(user_id)
        favorites = user.get('favorites', [])
        return jsonify({'saved_posts': favorites})
    
    else:
        return jsonify({'saved_posts': []})



# Route to upload a photo or take a photo 
@app.route('/create', methods=['POST', 'GET'])
def create():
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    session['image_on_post_page'] = False
    if request.method == 'POST':
        # If the data that the user is submitting is in json format, we retreive the json data. 
        if request.is_json:
            data = request.get_json()

            # If the data is an image: 
            if 'image' in data:
                import base64
                image_data = base64.b64decode(data['image'].split(",")[-1]) # Decodes the base64-encoded image data (removes anything not needed)
                file_name = generate_unique_filename("image.jpg")           # Generates a unique filename for the image. 
                
                # Uploads the image as a jpeg to the AWS S3 Bucket, based on the BUCKET_NAME. 
                s3.put_object(Bucket=os.getenv('BUCKET_NAME'), Key=file_name, Body=image_data, ContentType='image/jpeg')
                
                # Update session variables
                session['uploaded_file_key'] = file_name
                session['image_viewed'] = False 
                session['image_on_post_page'] = False

                # Once either uploaded or taken a photo, if image upload is successful, we redirect to the post page where the user can add details to their post. 
                redirect_url = url_for('post')
                return jsonify({'redirect': redirect_url})

    return render_template('create.html')


# Route to gallery
@app.route('/gallery', methods = ['GET'])
def gallery():
    try:
        # Gets the user's logged in ID
        user_id = session.get('user_id')

        # If the user has logged in, then we can do the following
        if user_id:
            # We essentially get the current_user's favorite array and passes these details to the gallery.html page. 
            current_user = get_user_by_id(user_id)
            favorites = list(get_favorites_by_ids(current_user.get('favorites')))
            return render_template('gallery.html', favorites=favorites, get_user_by_id=get_user_by_id)
        return redirect(url_for('login'))
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to submit post", 500

# Handle unlike put request
@app.put('/unlike/<string:post_id>')
def unlike_post(post_id):
    try:
        user_id = session.get('user_id')
        if user_id:
            # update user's like
            current_user = get_user_by_id(user_id)
            if current_user.get('favorites') is not None and ObjectId(post_id) in current_user['favorites']:
                database['users'].update_one({'_id': ObjectId(user_id)}, {'$pull': {'favorites': ObjectId(post_id)}})
            # update post's like
            unlike_post_by_id(post_id)

        return redirect(url_for('login'))
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to submit post", 500


@app.route('/post', methods=['POST', 'GET'])
def post():
    try:
        session['image_on_post_page'] = True
        # In case the file key (filename) has not been uploaded, we present an error. 
        if 'uploaded_file_key' not in session:
            abort(400, description="Image not found in session")

        # Else, we create a URL for the image: through the BUCKET_NAME and the uploaded_file_key session variable (which is the filename)
        image_url = f"https://{os.getenv('BUCKET_NAME')}.s3.amazonaws.com/{session['uploaded_file_key']}"

        session['image_viewed'] = True
        return render_template('post.html', image_url=image_url) # We pass the image URL to the html page to paste it on the front page to let the user confirm it.

    except Exception as e:
        print(f"An error occurred: {e}")
        abort(500, description="Internal server error")
        
# Route to upload posts - this is when the user actually edits the data regarding the post such as the description/title. 
@app.route('/post_data', methods=['POST'])
def post_data():
    # This accesses the posts cluster in the database
    posts_collection = database['posts']
    
    # This gets the user's username, user_id, post description from post.html and the image url
    try:
        username = session.get('username')
        user_id = session.get('user_id')
        post_description = request.form.get('post_description')
        post_title = request.form.get('post_title')
        image_type = request.form.get('image_type')
        image_url = session.get('uploaded_file_key', None)
        
        # If the image_url is valid, we update the image_url to its filename
        if image_url:
            image_url = f"https://{os.getenv('BUCKET_NAME')}.s3.amazonaws.com/{image_url}"
        
        # We create a post document to upload to the mongoDB atlas database
        post = {
            "user_id": user_id, 
            "username": username,
            "likes": 0,
            "post_title": post_title, 
            "post_description": post_description,
            "image_url": image_url,
            "art_type": image_type,
            "created_at": datetime.datetime.utcnow()  
        }

        # We insert the page and then redirect to the home page. 
        posts_collection.insert_one(post)
        return redirect(url_for('home'))
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to submit post", 500

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
        user_posts = database.posts.find({"user_id":f"{user_id}"}).sort("created_at", -1)

        if not user_posts:
            return render_template('profile.html', user=user, user_posts=[])
        else:
            return render_template('profile.html', user=user, user_posts=user_posts)

    # Else, if they don't have an account, it will redirect them to the login page
    else: 
        return render_template('login.html')
    
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' in session: 
        user_id = ObjectId(session['user_id'])
        user = database.users.find_one({'_id': user_id})

        if request.method == 'POST':

            new_username = request.form['new_username']

            errors = []
            
            # Check if any username was provided
            if new_username != '':
                # This checks if there is already a user that has this exact username
                if database.users.find_one({'username': new_username}):
                    errors.append("Username already exists! Choose another one!")
                    errors.append(f"{new_username}")
            
            if errors:
                return render_template('edit_profile.html', user=user, errors=errors)
            
            else:
                if new_username != '':
                    filter = {'_id': user_id}
                            
                    update = {'$set': {'username': f"{new_username}"}}

                    database.users.update_one(filter, update)

                    filt = {'user_id': f"{user_id}"}

                    upd = {'$set': {'username': f"{new_username}"}}

                    database.posts.update_many(filt, upd)

                    session.update({"username": new_username})

                    return redirect(url_for('profile'))    
                
        return render_template('edit_profile.html', user=user)      
    

@app.route('/delete_account', methods=['POST'])
def delete_account():
    # Check if user is authenticated
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = ObjectId(session['user_id'])

    user = database.users.find_one({'_id': user_id})
    if not user:
        return "User not found", 404

    try:
        avatar_url = user.get('avatar_url')
        if avatar_url:
            parsed_url = urlparse(avatar_url)
            avatar_key = parsed_url.path.lstrip('/')
            s3.delete_object(Bucket=os.getenv('BUCKET_NAME'), Key=avatar_key)

        database.users.delete_one({'_id': user_id})
        session.pop('user_id', None)
        session.pop('uploaded_file_key', None)

        return redirect(url_for('home', message="Account successfully deleted."))

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

 
@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    posts_collection = database.posts

    try:
        post = posts_collection.find_one({'_id': ObjectId(post_id)})

        if not post:
            return "Post not found", 404

        image_key = post['image_url'].split(f"https://{os.getenv('BUCKET_NAME')}.s3.amazonaws.com/")[-1]
        s3.delete_object(Bucket=os.getenv('BUCKET_NAME'), Key=image_key)
        posts_collection.delete_one({'_id': ObjectId(post_id)})

        # Redirect back to profile page
        return redirect(url_for('profile'))

    except Exception as e:
        print(f"An error occurred during post deletion: {e}")
        return "Failed to delete post", 500

@app.route('/update_pp', methods=['GET', 'POST'])
def update_pp():
    if 'user_id' not in session:
        return "User not authenticated", 403

    user_id = ObjectId(session['user_id'])
    user = database.users.find_one({'_id': user_id})

    if 'profilePicture' not in request.files:
        return "No file part", 400

    file = request.files['profilePicture']
    if file.filename == '':
        return "No selected file", 400

    try:
        # If there's an existing profile picture, delete it from S3
        old_avatar_url = user.get('avatar_url')
        if old_avatar_url:
            parsed_url = urlparse(old_avatar_url)
            old_avatar_key = parsed_url.path.lstrip('/')
            s3.delete_object(Bucket=os.getenv('BUCKET_NAME'), Key=old_avatar_key)

        # Upload the new image to AWS S3
        image_data = file.read()
        file_name = generate_unique_filename(file.filename)

        s3.put_object(Bucket=os.getenv('BUCKET_NAME'), Key=file_name, Body=image_data, ContentType='image/jpeg')

        # Save the new image URL to MongoDB
        session['uploaded_file_key'] = file_name
        image_url = f"https://{os.getenv('BUCKET_NAME')}.s3.amazonaws.com/{session['uploaded_file_key']}"

        filter = {'_id': user_id}
        update = {'$set': {'avatar_url': f"{image_url}"}}
        collection = database['users']
        collection.update_one(filter, update)

        return redirect(url_for('profile'))

    except Exception:
        return "AWS credentials not available", 500
 
    
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
            collection = database['users']
            collection.insert_one({
                'username': username,
                'password': password_hash,
                'email': email,
                'favorites': [],
                'avatar_url': "https://i.stack.imgur.com/l60Hf.png"
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
            
@app.route('/forgot_password', methods = ['GET','POST'])
def forgot_password():
    if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            email = request.form['email']

            errors = []
            
            user = database.users.find_one({'email': email, 'username':username})

            if not user:
                errors.append("Invalid username or email!")
            
            if len(password) < 8 & len(password) > 20:
                errors.append("Password must be between 8 and 20 characters long!")
            
            if not any(char.isdigit() for char in password):
                errors.append("Password should have at least one number!")
            
            if not any(char.isalpha() for char in password):
                errors.append("Password should have at least one alphabet!")
            
            if not confirm_password == password:
                errors.append("Passwords do not match!")

            if errors:
                return render_template('forgot_password.html', errors=errors)
            
            else:
                password_hash = generate_password_hash(password)

                filter = {'email': email, 'username':username}
                          
                update = {'$set': {'password': password_hash}}

                database.users.update_one(filter, update)
                                     
                return redirect(url_for('login'))
            
    return render_template('forgot_password.html')

# Here we have another route, if the user decides to logout, it will pop their user_id from the session and redirect them to the login page
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# This are routes to handle any errors that may occur during any HTTP requests
@app.errorhandler(Exception)
def handle_error(err):
    return render_template('error.html', error=err)

@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', message=e.description), 400

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', message=e.description), 500

# Executing the Flask Application: 
if(__name__ == "__main__"):
    app.run(debug=True)
