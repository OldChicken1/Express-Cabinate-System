from flask import Flask, jsonify, request, Response
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps
import RPi.GPIO as GPIO
import time
import sys
import os
client = MongoClient('localhost', 27017)
#Get database "ECE4534_test" (or create it)
db = client['final']
collection = db['client']
def box1(status):
    if status == "on":
        GPIO.output(2,GPIO.HIGH)
    else:
        GPIO.output(2,GPIO.LOW)
	
def box2(status):
    if status == "on":
        GPIO.output(3,GPIO.HIGH)
    else:
        GPIO.output(3,GPIO.LOW)
	
def box3(status):
    if status == "on":
        GPIO.output(4,GPIO.HIGH)
    else:
        GPIO.output(4,GPIO.LOW)
    
def red():#26
    GPIO.output(26,GPIO.HIGH)
    GPIO.output(21,GPIO.LOW)
    GPIO.output(18,GPIO.LOW)
	
def green():#21
    GPIO.output(21,GPIO.HIGH)
    GPIO.output(26,GPIO.LOW)
    GPIO.output(18,GPIO.LOW)
	
def yellow():
    GPIO.output(21,GPIO.HIGH)
    GPIO.output(26,GPIO.HIGH)
    GPIO.output(18,GPIO.LOW)
    
def getDocument(name, collection):
    #Look for 1 document (there should only be 1 in the database)
    cursor = collection.find({"name": name}).limit(1)
    #You can also use a for loop that will run once
    return  next(cursor,None)

def light(document_name, collection):
    document = getDocument(document_name, collection)
    if document:
        if document["status"] == "on":
            hi = document["status"]
        elif document["status"] == "off":
            hi = document["status"]
        else:
            print ("Bad data in database")
        if document_name == "box1":
            box1(hi)
        elif document_name == "box2":
            box2(hi)
        elif document_name == "box3":
            box3(hi)
        return
def putServer(document_name, collection, status):
    debugData = {'name': document_name, 'status': status}
    oldDebug_cursor = collection.find({"name": document_name}).limit(1)
    oldDebug = next(oldDebug_cursor,None)
    if oldDebug:
        collection.update_one({"name": document_name}, {"$set": debugData})
    else:
        collection.insert_one(debugData)

def open_slot(num):
    if num == 1:
        putServer("box1", collection, "on")
        light("box1", collection)
    elif num == 2:
        putServer("box2", collection, "on")
        light("box2", collection)
    elif num == 3:
        putServer("box3", collection, "on")
        light("box3", collection)
    else:
        print("Bad slot input", num)

def close_slot(num):
    if num == 1:
        putServer("box1", collection, "off")
        light("box1", collection)
    elif num == 2:
        putServer("box2", collection, "off")
        light("box2", collection)
    elif num == 3:
        putServer("box3", collection, "off")
        light("box3", collection)
    else:
        print("Bad slot input", num)
def empty_slotCheck():
    cursor = collection.find({"status": "off"}).limit(1)
    return next(cursor,None)
        
def update_status():
    yellow()
    x = input("Press enter when is finished!")
    green()

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(21,GPIO.OUT)
    GPIO.setup(26,GPIO.OUT)
    GPIO.setup(18,GPIO.OUT)
    GPIO.setup(2,GPIO.OUT)
    GPIO.setup(3,GPIO.OUT)
    GPIO.setup(4,GPIO.OUT)
    putServer("box1", collection, "off")
    putServer("box2", collection, "off")
    putServer("box3", collection, "off")
    light("box1", collection)
    light("box2", collection)
    light("box3", collection)
    
if __name__ == '__main__':
    main()
