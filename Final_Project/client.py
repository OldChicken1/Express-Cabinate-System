import pyzbar.pyzbar as pyzbar
import cv2
import hashlib
import socket
import pickle
import os
import sys
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
from watson_developer_cloud import  TextToSpeechV1
import wolframalpha
import clientKeys
from client2 import open_slot
from client2 import close_slot
from client2 import update_status
from client2 import green
from client2 import empty_slotCheck
from client2 import red
import pymongo
from pymongo import MongoClient
from cryptography.fernet import Fernet
import RPi.GPIO as GPIO
import json
client = MongoClient('localhost', 27017)
#Get database "ECE4534_test" (or create it)
db = client['final']
collection = db['client']
def welcome_msg():
    os.system("omxplayer -o local welcome.wav")

def qr_code_msg():
    os.system("omxplayer -o local qr_code.wav")
    
def full_warning():
    os.system("omxplayer -o local full.wav")
    
def phone_number():
    os.system("omxplayer -o local phone.wav")
    
def accessCode():
    os.system("omxplayer -o local code.wav")
    
def validation():
    os.system("omxplayer -o local validation.wav")
    
def openSlot_msg(slot):
    text = 'Slot ' + str(slot) + ' is opened, please press enter after storing or retrieving packagess'
    sound = TextToSpeechV1(url = clientKeys.wal_url, iam_apikey = clientKeys.wal_key)
    with open('open_slot.wav', 'wb') as audio_file:
        sound_recieve = sound.synthesize(str(text), accept = 'audio/wav', voice = "en-US_AllisonVoice").get_result()
        audio_file.write(sound_recieve.content)
    #print ('Checkpoint 08 Speaking Answer: ', answer, '\n')
    os.system("omxplayer -o local open_slot.wav")
    audio_file.close()
    
def cameraSetup():
    camera = PiCamera()
    camera.resolution = (640,480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640,480))
    time.sleep(0.1)
    return camera, rawCapture

def decode(img):
    decoded = pyzbar.decode(img)
    data = []
    for each in decoded:
        data = each.data
    return data

def display(img, decoded):
    points = []
    for each in decoded:
        points = each.polygon

    if len(points) > 4 :
        hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
        hull = list(map(tuple, np.squeeze(hull)))
    else :
        hull = points
    n = len(hull)
    for j in range(0,n):
        cv2.line(img, hull[j], hull[ (j+1) % n], (255,0,0), 3)
        cv2.imshow("Results", img);
        cv2.waitKey(0)

def scanQR(cam, rawCapture):
    for frame in camera.capture_continuous(rawCapture, format = "bgr", use_video_port = True):      
        image = frame.array
        cv2.imshow("Frame", image)
        key = cv2.waitKey(1) & 0xFF
        img_data = decode(image)
        rawCapture.truncate(0)
        if img_data:
            print('QR-code recongnized!!!')
            return img_data
            

def encrypt(data):
    key = Fernet.generate_key()
    f = Fernet(key)
    print(type(data))
    token = f.encrypt(data)
    #print(type(token))
    m = hashlib.md5()
    m.update(token)
    token_hash = m.hexdigest()
    #print(type(token_hash))
    #print ('Generated Key: ', key, '| Cipher text: ', token, '\n')
    payload = (key, token, token_hash)
    pay_load_toSend = pickle.dumps(payload)
    return f, pay_load_toSend
    
def decrypt(f, data):
    da = pickle.loads(data)
    #print ('Checkpoint 06 Received data: ', da, '\n')
    encrypted = da[0]
    check = str(da[1])
    answer = f.decrypt(encrypted)
    #print('answer: ', answer)
    newM = hashlib.md5()
    newM.update(encrypted)
    answer_hash = newM.hexdigest()
    if answer_hash == check:
        return answer
    else:
        return "Check sum failed, data may been hacked."
    


def change_to_int(data):
    if data == 'slot1':
        return 1
    elif data == 'slot2':
        return 2
    elif data == 'slot3':
        return 3
        
if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(21,GPIO.OUT)
    GPIO.setup(26,GPIO.OUT)
    GPIO.setup(18,GPIO.OUT)
    GPIO.setup(2,GPIO.OUT)
    GPIO.setup(3,GPIO.OUT)
    GPIO.setup(4,GPIO.OUT)
    green()
    close_slot(1)
    close_slot(2)
    close_slot(3)
    sip = sys.argv[2]
    #sip = '172.29.68.150'
    #sip = '10.0.0.126'
    #sp = '5005'
    #size = 1024
    sp = sys.argv[4]
    size = int(sys.argv[6])
    host = sip
    port = int(sp)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    camera, rawCapture = cameraSetup()
    while True:
        empty = empty_slotCheck()
        if empty == None:
            red()
        status = input("Press 1 for STORE, Press 2 for RETRIEVE: ")
        welcome_msg()
        if int(status) == 1:
            storing = 'Storing'
            f, pay_load_toSend = encrypt(bytes(storing,'utf-8'))
            print(f, pay_load_toSend)
            s.send(pay_load_toSend)
            ack = s.recv(size)
            print(ack)
            if ack:
                ack = decrypt(f, ack)
                ack = ack.decode('utf-8')
                if ack != "Acknowledged":
                    print('Sorry, currently all slots are occupied. Please try later.')
                    full_warning()
                else:
                    img_data = scanQR(camera, rawCapture)
                    qr_code_msg()
                    print('img_data: ', img_data)
                    f, pay_load_toSend = encrypt(img_data)
                    s.send(pay_load_toSend)
                    data = s.recv(size)
                    if data:
                        slot = decrypt(f, data)
                        print(str(slot))
                        slot = slot.decode('utf-8')
                        slot_to_open = change_to_int(slot)
                        open_slot(slot_to_open)
                        openSlot_msg(slot_to_open)
                        update_status()
                        signal = 'storing finished'
                        f, signal_toSend = encrypt(bytes(signal,'utf-8'))
                        s.send(signal_toSend)
        elif int(status) == 2:
            storing = 'Retrieve'
            f, pay_load_toSend = encrypt(bytes(storing,'utf-8'))
            s.send(pay_load_toSend)
            ack = s.recv(size)
            if ack:
                phone_number()
                number = input("Please type in your phone number: ")
                accessCode()
                access_code = input("Please type in your 6 digit access code: ")
                info_check = {"number": number, "access_code": access_code}
                info_check = json.dumps(info_check)
                f, pay_load_toSend = encrypt(bytes(info_check,'utf-8'))
                print('pay_load_toSend: ', pay_load_toSend)
                s.send(pay_load_toSend)
                data = s.recv(size)
                if data:
                    slot = decrypt(f, data)
                    slot = slot.decode('utf-8')
                    
                    if slot != "error":
                        slot_to_open = change_to_int(slot)
                        openSlot_msg(slot_to_open)
                        update_status()
                        close_slot(slot_to_open)
                        signal = 'retrieve finished'
                        f, signal_toSend = encrypt(bytes(signal,'utf-8'))
                        s.send(signal_toSend)
                    else:
                        print('Information validation failed. We may not have your package, or you entered the wrong phone number/access code. Please try again.')
                        validation()
    s.close()
    
    
