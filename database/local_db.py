'''
this connects to either a remote/local database (depending on what is chosen).
this can add documents to the collection's database and delete all of them.
this also retrieves the latest document from the collection
'''

import requests
import pymongo
from pymongo import UpdateOne
from bs4 import BeautifulSoup
import logger_setup
import pytz
from pymongo.mongo_client import MongoClient
from datetime import datetime, timedelta, timezone
from time import mktime
from dotenv import load_dotenv
from os import getenv

load_dotenv('C:\\Users\\Puja\\Work\\Coding\\Python\\For Poolsifi\\tradingview to everywhere\\.env')
pwd = getenv('MONGODB_PWD')

# Set up logger for this file
local_db_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

class Database:
    def __init__(self, col, delete=False):
        # for a connection to local database (the connection string was from the mongo shell when i typed "mongosh"):
        # self.client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+1.10.3")

        # for a connection to remote database:
        self.client = MongoClient(f"mongodb+srv://sammy:{pwd}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority")
        
        try:
            self.client.admin.command('ping')
            local_db_logger.info("You successfully connected to MongoDB!") # Send a ping to confirm a successful connection
        except Exception as e:
            local_db_logger.exception(f'Failed to connect to MongoDB database. Error:')
            return
        
        self.db = self.client["tte"]

        if delete:
            self.delete_all(col)
            local_db_logger.info("Successfully deleted all documents")

    def change_type(self, col: str):
        '''This changes these fields to type float: `entryPrice`, `tp1Price`, `tp2Price`, `tp3Price`, `slPrice` and this to type int: `unixTime`. This method was created so that these fields had the correct type which would make them easier to process in Power BI'''
        collection = self.db[col]
        for doc in collection.find():
            update_result = collection.update_one(
                {'_id': doc['_id']},
                {
                    '$set': {
                        'entryPrice': float(doc['entryPrice']),
                        'tp1Price': float(doc['tp1Price']),
                        'tp2Price': float(doc['tp2Price']),
                        'tp3Price': float(doc['tp3Price']),
                        'slPrice': float(doc['slPrice']),
                        'unixTime': int(doc['unixTime'])
                    }
                }
            )

        # Check the matched count to determine if the update was successful
        if update_result.modified_count == 0:
            local_db_logger.error(f"Error: Document with _id {doc['_id']} was not updated.")

        local_db_logger.info("Changed the type of the date field to int")

    def add_doc(self, doc: dict, col: str):
        '''Adds `doc` to a specific collection'''
        try:
            self.db[col].insert_one(doc)
            local_db_logger.info(f"Successfully sent a doc to {col} collection!")
            return True
        except Exception as e:
            local_db_logger.exception(f'Failed to add document to MongoDB\'s {col} collection. Error:')
            return False

    def change_tv_links(self, col: str):
        '''This changes the `entrySnapshot` and `exitSnapshot` fields in every document to a png link. I made this because papa decided that the png link of the TradingView snapshot is better than the html link.'''
        collection = self.db[col]
        bulk_operations = []

        # Query to find documents where exitSnapshot contains .png and entrySnapshot does not contain .png
        query = {
            'tvExitSnapshot': {'$regex': r'\.png', '$options': 'i'},
            'tvEntrySnapshot': {'$not': {'$regex': r'\.png', '$options': 'i'}}
        }

        for doc in collection.find(query, {'_id': 1, 'tvEntrySnapshot': 1}):
            entry_url = doc.get('tvEntrySnapshot')
            new_entry_link = self.extract_img_src(entry_url, 'entry')

            if new_entry_link:
                bulk_operations.append(
                    UpdateOne(
                        {'_id': doc['_id']},
                        {'$set': {'tvEntrySnapshot': new_entry_link}}
                    )
                )
            else:
                print(f"Failed to extract new links for document with _id {doc['_id']}")

        if bulk_operations:
            try:
                result = collection.bulk_write(bulk_operations)
                print(f"Bulk write operation completed. Matched: {result.matched_count}, Modified: {result.modified_count}")
            except Exception as e:
                print("Error during bulk write operation:")
                print(e)

    def extract_img_src(self, url: str, t) -> str:
        '''Extracts the src attribute of the img tag with the tv-snapshot-image class'''
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tag = soup.find('img', class_='tv-snapshot-image')
            if img_tag and 'src' in img_tag.attrs:
                new_link = img_tag['src']
                return new_link
            else:
                print(f"No img tag with class 'tv-snapshot-image' found in {url}.")
                return ''
        except Exception as e:
            print(f'Error fetching or parsing the URL {url} for {t}: {e}')
            return ''

    def get_latest_doc(self, col: str):
        '''This finds the latest doc in `col` collection based on the `unixTime` field'''
        docs = self.db[col].find_one(sort=[("unixTime", pymongo.DESCENDING)])
        return docs

    def delete_all(self, col: str):
        self.db[col].delete_many({}) 

    def delete_some(self, count: int, col: str):
        '''This will keep the latest `count` documents and deletes the rest of them. It will also log how many docs got deleted'''
        
        latest_100_ids = [x['_id'] for x in self.db[col].find().sort('unixTime', pymongo.DESCENDING).limit(count)] # Get the IDs of the latest 100 documents
        result = self.db[col].delete_many({'_id': {'$nin': latest_100_ids}}) # Delete all documents that are not in the latest 100
        local_db_logger.info(f"Deleted {result.deleted_count} documents from {col} collection.")

    def get_entries_in_timespan(self, col: str, category: str, start_time: int, end_time = int(mktime(datetime.now().timetuple()))):
        '''Returns entries within a specific time span which are from a certain category. `start_time` is the unix date that the entries should come after. `end_time` is the unix date that entries should come before and its default value is today'''
        try:
            local_db_logger.info(f'Retrieving entries from {col} collection with {category} category between {self.unix_to_readable(start_time)} and {self.unix_to_readable(end_time)}')
            # For unixTime: multiply by 1000 to convert to milliseconds because the date field in the mongodb documents is in milliseconds. 
            return self.db[col].find({"unixTime": {"$gte": start_time*1000, "$lte": end_time*1000 }, "category": category})
        except Exception as e:
            local_db_logger.exception(f'Error in get_entries_in_timespan:')
            return []
        
    def get_unix_time(self, days_ago: int):
        '''Returns the unix time of `days_ago` days ago'''
        target_date = datetime.now() - timedelta(days=days_ago)
        local_db_logger.info(f"The date {days_ago} days ago was: {target_date.strftime('%Y-%m-%d')}")
        unix_time = int(mktime(target_date.timetuple()))
        return unix_time
    
    def unix_to_readable(self, unix_timestamp):
        '''converts a unix timestamp to nicely formatted string in the Asia/Kolkata timezone'''
        timestamp_datetime = datetime.utcfromtimestamp(unix_timestamp) # Convert the Unix timestamp to a datetime object
        timezone = pytz.timezone('Asia/Kolkata') # Convert UTC to Asia/Kolkata timezone
        timestamp_datetime_kolkata = timestamp_datetime.replace(tzinfo=pytz.utc).astimezone(timezone) # Format the datetime object into a short, readable string
        readable_format = timestamp_datetime_kolkata.strftime('%y-%m-%d %H:%M')
        return readable_format

