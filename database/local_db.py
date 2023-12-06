'''
this connects to either a remote/local database (depending on what is chosen).
this can add documents to the collection's database and delete all of them.
this also retrieves the latest document from the collection
'''

import pymongo
import logger_setup
from pymongo.mongo_client import MongoClient

# Set up logger for this file
local_db_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

PWD = 'kdgzKyjYr8WA6Vkm'

class Database:
    def __init__(self, delete=False):
        # for a connection to local database (the connection string was from the mongo shell when i typed "mongosh"):
        # self.client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+1.10.3")

        # for a connection to remote database:
        self.client = MongoClient(f"mongodb+srv://sammy:{PWD}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority")
        
        try:
            self.client.admin.command('ping')
            local_db_logger.info("You successfully connected to MongoDB!") # Send a ping to confirm a successful connection
        except Exception as e:
            local_db_logger.exception(f'Failed to connect to MongoDB database. Error:')
            return
        
        self.db = self.client["tradingview-to-everywhere"]
        self.collection = self.db["entries"]

        if delete:
            self.delete_all()
            local_db_logger.info("Successfully deleted all documents")

    def add_doc(self, doc: dict):
        try:
            self.collection.insert_one(doc)
            local_db_logger.info(f"Successfully sent a doc to MongoDb!")
            return True
        except Exception as e:
            local_db_logger.exception(f'Failed to add document to our local database\'s collection. Error:')
            return False

    def get_latest_doc(self):
        docs = self.collection.find_one(sort=[("_id", pymongo.DESCENDING)])
        return docs

    def delete_all(self):
        self.collection.delete_many({}) 

