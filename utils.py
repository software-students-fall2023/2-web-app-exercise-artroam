from pymongo import MongoClient
from bson.objectid import ObjectId   
import os

# client = MongoClient('mongodb://localhost:27017/')
# db = client['your_database_name']
client = MongoClient(os.getenv('MONGO_URI'))
database = client[os.getenv('MONGO_DBNAME')]

def get_user_by_id(user_id):
    return database.users.find_one({'_id': ObjectId(user_id)})