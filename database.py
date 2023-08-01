import pymongo
from pymongo import MongoClient

PWD = '1304sammy#'

class Database:
    def __init__(self):
        self.pwd = PWD
        self.cluster = MongoClient(f"mongodb+srv://samaara:{self.pwd}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.cluster["test"]
        self.collection = self.db["collection 1"]

    def add_doc(self, *args):
        '''
        args must have these arguments in this order:
        ```
        trade_counter
        type
        direction
        symbol
        tframe
        entry
        tp
        sl
        chart_link
        date
        ```
        '''

        doc = {
            "_id": args[0],
            "type": args[1],
            "direction": args[2],
            "symbol": args[3],
            "tframe": args[4],
            "entry": args[5],
            "tp": args[6],
            "sl": args[7],
            "chart_link": args[8],
            "date": args[9]
        }
        self.collection.insert_one(doc)

    def get_latest_docs(self):
        docs = self.collection.find_one(sort=[("_id", pymongo.DESCENDING)])
        return docs
    
    def delete_all(self):
        self.collection.delete_many({}) 