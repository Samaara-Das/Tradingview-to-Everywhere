"""
This module connects to Firebase Firestore database and provides methods to interact with it.
It replaces the previous MongoDB implementation with equivalent functionality for Firestore.

This module can add documents to collections, retrieve the latest document,
retrieve entries within a specific timespan, delete documents, and format timestamps.
"""

import os
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from time import mktime
import logger_setup

# Set up logger for this file
firebase_db_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)


class Database:
    def __init__(self, col, delete=False):
        """Initialize Firebase connection and database access.

        Args:
            col (str): Collection name (used for operation context)
            delete (bool, optional): Whether to delete all documents in the collection. Defaults to False.
        """
        # Get Firebase credentials from environment variable or use the service account file
        try:
            cred_path = os.getenv(
                "FIREBASE_CREDENTIALS_PATH",
                "tradingview-to-everywhere-firebase-adminsdk-fbsvc-f83f2609de.json",
            )
            project_id = os.getenv("FIREBASE_PROJECT_ID")

            # Initialize Firebase app if not already initialized
            if not firebase_admin._apps:
                if project_id:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {"projectId": project_id})
                else:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)

            # Get Firestore client
            self.db = firestore.client()
            firebase_db_logger.info("You successfully connected to Firebase Firestore!")
        except Exception as e:
            firebase_db_logger.exception(
                f"Failed to connect to Firebase Firestore database. Error:"
            )
            return

        # Delete all documents in the collection if requested
        if delete and col:
            self.delete_all(col)
            firebase_db_logger.info("Successfully deleted all documents")

    def change_type(self, col: str):
        """Change field types to appropriate types for Firestore.

        Args:
            col (str): Collection name
        """
        try:
            collection_ref = self.db.collection(col)
            docs = collection_ref.stream()

            for doc in docs:
                doc_data = doc.to_dict()

                # Update field types
                update_data = {
                    "entryPrice": float(doc_data.get("entryPrice", 0)),
                    "tp1Price": float(doc_data.get("tp1Price", 0)),
                    "tp2Price": float(doc_data.get("tp2Price", 0)),
                    "tp3Price": float(doc_data.get("tp3Price", 0)),
                    "slPrice": float(doc_data.get("slPrice", 0)),
                    "unixTime": int(doc_data.get("unixTime", 0)),
                }

                # Update document
                collection_ref.document(doc.id).update(update_data)

            firebase_db_logger.info("Changed the type of the date field to int")
        except Exception as e:
            firebase_db_logger.exception(f"Error in change_type method: {e}")

    def add_doc(self, doc: dict, col: str):
        """Add a document to the specified collection.

        Args:
            doc (dict): Document to add
            col (str): Collection name

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.db.collection(col).add(doc)
            firebase_db_logger.info(f"Successfully sent a doc to {col} collection!")
            return True
        except Exception as e:
            firebase_db_logger.exception(
                f"Failed to add document to Firebase's {col} collection. Error:"
            )
            return False

    def change_tv_links(self, col: str):
        """Change the TV links to PNG links.

        Args:
            col (str): Collection name
        """
        try:
            collection_ref = self.db.collection(col)
            query = collection_ref.where("tvExitSnapshot", ">=", ".png")

            for doc in query.stream():
                doc_data = doc.to_dict()

                # Check if entry snapshot doesn't contain .png
                if (
                    "tvEntrySnapshot" in doc_data
                    and ".png" not in doc_data["tvEntrySnapshot"]
                ):
                    entry_url = doc_data.get("tvEntrySnapshot")
                    new_entry_link = self.extract_img_src(entry_url, "entry")

                    if new_entry_link:
                        collection_ref.document(doc.id).update(
                            {"tvEntrySnapshot": new_entry_link}
                        )

            firebase_db_logger.info(
                f"Successfully updated TV links in {col} collection"
            )
        except Exception as e:
            firebase_db_logger.exception(f"Error in change_tv_links: {e}")

    def extract_img_src(self, url: str, t) -> str:
        """Extract image source from URL.

        Args:
            url (str): URL to extract image from
            t: Type identifier for logging

        Returns:
            str: Extracted image URL or empty string
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            img_tag = soup.find("img", class_="tv-snapshot-image")

            if img_tag and "src" in img_tag.attrs:
                new_link = img_tag["src"]
                return new_link
            else:
                print(f"No img tag with class 'tv-snapshot-image' found in {url}.")
                return ""
        except Exception as e:
            print(f"Error fetching or parsing the URL {url} for {t}: {e}")
            return ""

    def get_latest_doc(self, col: str):
        """Get the latest document from the collection based on unixTime.

        Args:
            col (str): Collection name

        Returns:
            dict: Document data or None
        """
        try:
            docs = (
                self.db.collection(col)
                .order_by("unixTime", direction=firestore.Query.DESCENDING)
                .limit(1)
                .stream()
            )
            for doc in docs:
                # Convert to dict and add the document ID
                result = doc.to_dict()
                result["_id"] = doc.id
                return result
            return None
        except Exception as e:
            firebase_db_logger.exception(f"Error in get_latest_doc: {e}")
            return None

    def delete_all(self, col: str):
        """Delete all documents in a collection.

        Args:
            col (str): Collection name
        """
        try:
            batch_size = 500  # Firestore has a limit of 500 operations per batch
            docs = self.db.collection(col).limit(batch_size).stream()
            deleted = 0

            # Delete documents in batches to avoid out of memory errors
            for doc in docs:
                doc.reference.delete()
                deleted += 1

            if deleted >= batch_size:
                # Recursive call to delete more documents
                self.delete_all(col)

            firebase_db_logger.info(
                f"Deleted {deleted} documents from {col} collection"
            )
        except Exception as e:
            firebase_db_logger.exception(f"Error in delete_all: {e}")

    def delete_some(self, count: int, col: str):
        """Keep the latest 'count' documents and delete the rest.

        Args:
            count (int): Number of documents to keep
            col (str): Collection name
        """
        try:
            # Get the timestamp of the oldest document to keep
            docs = (
                self.db.collection(col)
                .order_by("unixTime", direction=firestore.Query.DESCENDING)
                .limit(count)
                .stream()
            )
            doc_ids = []
            oldest_timestamp = None

            for doc in docs:
                doc_data = doc.to_dict()
                doc_ids.append(doc.id)
                if (
                    oldest_timestamp is None
                    or doc_data.get("unixTime", 0) < oldest_timestamp
                ):
                    oldest_timestamp = doc_data.get("unixTime", 0)

            # If we found enough documents, delete all older ones
            if oldest_timestamp is not None:
                older_docs = (
                    self.db.collection(col)
                    .where("unixTime", "<", oldest_timestamp)
                    .stream()
                )
                deleted = 0

                for doc in older_docs:
                    doc.reference.delete()
                    deleted += 1

                firebase_db_logger.info(
                    f"Deleted {deleted} documents from {col} collection."
                )
            else:
                firebase_db_logger.info(f"No documents to delete in {col} collection.")
        except Exception as e:
            firebase_db_logger.exception(f"Error in delete_some: {e}")

    def get_entries_in_timespan(
        self,
        col: str,
        category: str,
        start_time: int,
        end_time=int(mktime(datetime.now().timetuple())),
    ):
        """Get entries in a specific timespan and category.

        Args:
            col (str): Collection name
            category (str): Category to filter by
            start_time (int): Start timestamp (Unix time in seconds)
            end_time (int, optional): End timestamp (Unix time in seconds). Defaults to current time.

        Returns:
            list: List of documents
        """
        try:
            firebase_db_logger.info(
                f"Retrieving entries from {col} collection with {category} category between {self.unix_to_readable(start_time)} and {self.unix_to_readable(end_time)}"
            )

            # Convert seconds to milliseconds for Firestore
            start_ms = start_time * 1000
            end_ms = end_time * 1000

            # Query documents
            docs = (
                self.db.collection(col)
                .where("category", "==", category)
                .where("unixTime", ">=", start_ms)
                .where("unixTime", "<=", end_ms)
                .stream()
            )

            # Convert to list of dicts and add document IDs
            result = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["_id"] = doc.id
                result.append(doc_data)

            return result
        except Exception as e:
            firebase_db_logger.exception(f"Error in get_entries_in_timespan: {e}")
            return []

    def get_unix_time(self, days_ago: int):
        """Get Unix timestamp from days ago.

        Args:
            days_ago (int): Number of days ago

        Returns:
            int: Unix timestamp
        """
        target_date = datetime.now() - timedelta(days=days_ago)
        firebase_db_logger.info(
            f"The date {days_ago} days ago was: {target_date.strftime('%Y-%m-%d')}"
        )
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
        timezone = pytz.timezone("Asia/Kolkata")
        timestamp_datetime_kolkata = timestamp_datetime.replace(
            tzinfo=pytz.utc
        ).astimezone(timezone)
        readable_format = timestamp_datetime_kolkata.strftime("%y-%m-%d %H:%M")
        return readable_format
