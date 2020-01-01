import socket
import sys
import pickle
import hashlib
import os
import pymongo
from pymongo import MongoClient
import sys
import json
import random
import serverKeys
from twilio.rest import Client
from cryptography.fernet import Fernet
client = MongoClient('localhost', 27017)
#Get database "ECE4534_test" (or create it)
db = client['final']
collection = db['server']
twilioClient = Client(serverKeys.token1, serverKeys.key1)
def decrypt(data):
    da=pickle.loads(data)
    #current_check: 60972f3d9bcb8d113369105ee5d6c5e8
    
    encrypted=da[1]
    key=Fernet(da[0])
    check=str(da[2])
    question=key.decrypt(encrypted)
    m = hashlib.md5()
    m.update(encrypted)
    quest_hash = m.hexdigest()
    if quest_hash == check:
        return key, question
    else:
        return None

def encrypt(key, data):
    encrypted_answer = key.encrypt(bytes(data, 'utf-8'))
    newM = hashlib.md5()
    newM.update(encrypted_answer)
    answer_hash = newM.hexdigest()
    payload_answer = (encrypted_answer, answer_hash)
    payload_answer_tosend = pickle.dumps(payload_answer)
    return payload_answer_tosend
    
def getDocument(name, collection):
    #Look for 1 document (there should only be 1 in the database)
    cursor = collection.find({"name": name}).limit(1)
    #You can also use a for loop that will run once
    return  next(cursor,None)

def putOff(document_name, collection):
    debugData = {'name': document_name, 'status': "off"}
    oldDebug_cursor = collection.find({"name": document_name}).limit(1)
    oldDebug = next(oldDebug_cursor,None)
    if oldDebug:
        collection.update_one({"name": document_name}, {"$set": debugData})
    else:
        collection.insert_one(debugData)
        
def putOn(document_name, collection, data):
    data["name"]=document_name
    data["status"]="on"
    debugData=data
    print ("data", debugData)
    oldDebug_cursor = collection.find({"name": document_name}).limit(1)
    oldDebug = next(oldDebug_cursor,None)
    if oldDebug:
        collection.update_one({"name": document_name}, {"$set": debugData})
    else:
        collection.insert_one(debugData)

def findSlot():
    array = ["slot1", "slot2", "slot3"]
    for x in array:
        y = getDocument(x, collection)
        if y["status"] == "off":
            return x
    return None

def vertifySlot(number, code):
    array = ["slot1", "slot2", "slot3"]
    for x in array:
        y = getDocument(x, collection)
        print(y["phone"], y["code"])
        if str(y["phone"]) == number and str(y["code"]) == code:
            return x
    return None

if __name__ == '__main__':
    #pt = 5005
    pt = int(sys.argv[2])
    #size = 1024#
    size = int(sys.argv[4])
    ip_port = ('', pt)
    web = socket.socket()
    web.bind(ip_port)
    web.listen(5)
    conn,addr = web.accept()
    while True:
        command = conn.recv(size)
        if command:
            key, comm = decrypt(command)
            print('command: ', str(comm))
            comm = comm.decode('utf-8')
            if str(comm) == "Storing":
                slot = findSlot()
                if slot is None:
                    error_msg = 'Sorry, currently all slots are occupied. Please try later.'
                    error_msg_toSend = encrypt(key, error_msg)
                    conn.send(error_msg_toSend)
                else:
                    ack = "Acknowledged"
                    ack_to_send = encrypt(key, ack)
                    conn.send(ack_to_send)
                    
                    data = conn.recv(size)
                    if data:
                        key, da = decrypt(data)
                        da = da.decode('utf-8')
                        print('Information received: '+str(da))
                        #print('data type :')
                        #print(type(da))
                        slot = findSlot()
                        if slot is not None:
                            slot_to_send = encrypt(key, str(slot))
                            conn.send(slot_to_send)
                            signal = conn.recv(size)
                            if signal:
                                access_code = random.randint(100000, 999999)
                                da=json.loads(da)
                                da['code'] = access_code
                                putOn(slot, collection, da)
                                twilioClient.messages.create(from_=serverKeys.phone,
                                                                to = da['phone'],
                                                                body = serverKeys.message + str(access_code))
            elif str(comm) == "Retrieve":
                ack = "Acknowledged"
                ack_to_send = encrypt(key, ack)
                conn.send(ack_to_send)
                
                data = conn.recv(size)
                if data:
                    key, da = decrypt(data)
                    da = da.decode('utf-8')
                    print('Information received: '+str(da))
                    #print('data type :')
                    #print(type(da))
                    da = json.loads(da)
                    number = da["number"]
                    access_code = da["access_code"]
                    print ("number", number)
                    print ("access_code", access_code)
                    result = vertifySlot(str(number), str(access_code))
                    print ("result", result)
                    if result is not None:
                        slot_to_send = encrypt(key, str(result))
                        conn.send(slot_to_send)
                        signal = conn.recv(size)
                        if signal:
                            putOff(result, collection)
                    else:
                        error_msg = "error"
                        msg_to_send = encrypt(key, str(error_msg))
                        conn.send(msg_to_send)
