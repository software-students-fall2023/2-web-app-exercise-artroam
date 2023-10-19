from pymongo import MongoClient
from bson.objectid import ObjectId   
import os

client = MongoClient(os.getenv('MONGO_URI'))
database = client[os.getenv('MONGO_DBNAME')]

# get user by id from MongoDB
def get_user_by_id(user_id):
    return database['users'].find_one({'_id': ObjectId(user_id)})

def unlike_post_by_id(post_id):
    post = database['posts'].find_one({'_id': ObjectId(post_id)})
    if post:
        current_likes = post['likes']
        if current_likes > 0:
            database['posts'].update_one({'_id': ObjectId(post_id)}, {'$set': {'likes': current_likes - 1}})
    else:
        return 'no post found'

def get_favorites_by_ids(favorite_ids):
    if favorite_ids is None:
        return []
    else:
        return database['posts'].find({"_id": {"$in": favorite_ids}})