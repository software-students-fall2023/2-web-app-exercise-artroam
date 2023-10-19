from pymongo import MongoClient
from bson.objectid import ObjectId   
import os

client = MongoClient(os.getenv('MONGO_URI'))
database = client[os.getenv('MONGO_DBNAME')]

# get user by id from MongoDB
def get_user_by_id(user_id):
    return database['users'].find_one({'_id': ObjectId(user_id)})

def get_favorites_by_ids(favorite_ids):
    if favorite_ids is None:
        return []
    else:
        return database['posts'].find({"_id": {"$in": favorite_ids}})
