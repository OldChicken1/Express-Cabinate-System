import pymongo
from pymongo import MongoClient
from bson.json_util import dumps
import RPi.GPIO as GPIO
import time
import sys
import json
client = MongoClient('localhost', 27017)
db = client['final']
collection = db['server']

def putOff(document_name, collection):
    debugData = {'name': document_name, 'status': "off"}
    oldDebug_cursor = collection.find({"name": document_name}).limit(1)
    oldDebug = next(oldDebug_cursor,None)
    if oldDebug:
        collection.update_one({"name": document_name}, {"$set": debugData})
    else:
        collection.insert_one(debugData)
        
def main():
    putOff("slot1", collection)
    putOff("slot2", collection)
    putOff("slot3", collection)
        
if __name__ == '__main__':
    main()