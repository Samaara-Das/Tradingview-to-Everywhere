"""
This module connects to MongoDB database and provides methods to interact with it.
It replaces the Firebase implementation with equivalent functionality for MongoDB.

This module can add documents to collections, retrieve the latest document,
retrieve entries within a specific timespan, delete documents, and format timestamps.
"""

import os
import pytz
import pymongo
from pymongo import UpdateOne
from pymongo.mongo_client import MongoClient
from datetime import datetime, timedelta
from time import mktime
import logger_setup
import requests
from bs4 import BeautifulSoup
from env import COLLECTION

# Set up logger for this file
local_db_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

class Database:
    def __init__(self, delete=False):
        """Initialize MongoDB connection and database access.
        
        Args:
            delete (bool, optional): Whether to delete all documents in the collection. Defaults to False.
        """
        # Define the collection name from env configuration
        self.collection_name = COLLECTION
        # Get MongoDB connection details from environment variables
        try:
            # Check for MongoDB URI in environment variables first
            mongo_uri = os.getenv('MONGODB_URI')
            if not mongo_uri:
                # Fall back to password-based connection
                pwd = os.getenv('MONGODB_PWD')
                if pwd:
                    mongo_uri = f"mongodb+srv://sammy:{pwd}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority"
                else:
                    # Use local connection as fallback
                    mongo_uri = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000"
                    local_db_logger.warning("No MongoDB credentials found in environment, using local connection")
            
            self.client = MongoClient(mongo_uri)
            
            # Test connection
            self.client.admin.command('ping')
            local_db_logger.info("You successfully connected to MongoDB!")
            
            # Get database
            db_name = os.getenv('MONGODB_DATABASE', 'tte')
            self.db = self.client[db_name]
            
        except Exception as e:
            local_db_logger.exception(f'Failed to connect to MongoDB database. Error:')
            raise
        
        # Delete all documents in the collection if requested
        if delete:
            self.delete_all()
            local_db_logger.info("Successfully deleted all documents")

    def add_doc(self, doc: dict):
        """Add a document to the collection.
        
        Args:
            doc (dict): Document to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.db[self.collection_name].insert_one(doc)
            local_db_logger.info(f"Successfully sent a doc to {self.collection_name} collection!")
            return True
        except Exception as e:
            local_db_logger.exception(f'Failed to add document to MongoDB\'s {self.collection_name} collection. Error:')
            return False

    def change_tv_links(self):
        """Change the TV links to PNG links."""
        try:
            collection = self.db[self.collection_name]
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
            
            if bulk_operations:
                result = collection.bulk_write(bulk_operations)
                local_db_logger.info(f"Successfully updated TV links in {self.collection_name} collection. Modified: {result.modified_count}")
            else:
                local_db_logger.info(f"No TV links to update in {self.collection_name} collection")
                
        except Exception as e:
            local_db_logger.exception(f"Error in change_tv_links: {e}")

    def extract_img_src(self, url: str, t) -> str:
        """Extract image source from URL.
        
        Args:
            url (str): URL to extract image from
            t: Type identifier for logging
            
        Returns:
            str: Extracted image URL or empty string
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tag = soup.find('img', class_='tv-snapshot-image')
            
            if img_tag and 'src' in img_tag.attrs:
                new_link = img_tag['src']
                return new_link
            else:
                local_db_logger.debug(f"No img tag with class 'tv-snapshot-image' found in {url}.")
                return ''
        except Exception as e:
            local_db_logger.error(f'Error fetching or parsing the URL {url} for {t}: {e}')
            return ''

    def get_latest_doc(self):
        """Get the latest document from the collection based on unixTime.
        
        Returns:
            dict: Document data or None
        """
        try:
            doc = self.db[self.collection_name].find_one(sort=[("unixTime", pymongo.DESCENDING)])
            return doc
        except Exception as e:
            local_db_logger.exception(f"Error in get_latest_doc: {e}")
            return None

    def delete_all(self):
        """Delete all documents in the collection."""
        try:
            result = self.db[self.collection_name].delete_many({})
            local_db_logger.info(f"Deleted {result.deleted_count} documents from {self.collection_name} collection")
        except Exception as e:
            local_db_logger.exception(f"Error in delete_all: {e}") 

    def delete_some(self, count: int):
        """Keep the latest 'count' documents and delete the rest.
        
        Args:
            count (int): Number of documents to keep
        """
        try:
            # Get the IDs of the latest documents to keep
            latest_ids = [x['_id'] for x in self.db[self.collection_name].find().sort('unixTime', pymongo.DESCENDING).limit(count)]
            
            if latest_ids:
                # Delete all documents that are not in the latest set
                result = self.db[self.collection_name].delete_many({'_id': {'$nin': latest_ids}})
                local_db_logger.info(f"Deleted {result.deleted_count} documents from {self.collection_name} collection.")
            else:
                local_db_logger.info(f"No documents to delete in {self.collection_name} collection.")
                
        except Exception as e:
            local_db_logger.exception(f"Error in delete_some: {e}")

    def get_unix_time(self, days_ago: int):
        """Get Unix timestamp from days ago.
        
        Args:
            days_ago (int): Number of days ago
            
        Returns:
            int: Unix timestamp
        """
        target_date = datetime.now() - timedelta(days=days_ago)
        local_db_logger.info(f"The date {days_ago} days ago was: {target_date.strftime('%Y-%m-%d')}")
        unix_time = int(mktime(target_date.timetuple()))
        return unix_time
    
    def unix_to_readable(self, unix_timestamp):
        """Convert Unix timestamp to readable string.
        
        Args:
            unix_timestamp: Unix timestamp in seconds
            
        Returns:
            str: Formatted date string
        """
        timestamp_datetime = datetime.utcfromtimestamp(unix_timestamp)
        timezone = pytz.timezone('Asia/Kolkata')
        timestamp_datetime_kolkata = timestamp_datetime.replace(tzinfo=pytz.utc).astimezone(timezone)
        readable_format = timestamp_datetime_kolkata.strftime('%y-%m-%d %H:%M')
        return readable_format

