import asyncio
import cozmo
from Common.woc import WOC
from Common.colors import Colors
from os import system
import random
import _thread
import sys
from threading import Timer
import speech_recognition as sr
import os
from datetime import datetime
from dateutil import parser
import pytz

from GoogleCalendar import GoogleCalendar
# pip3 install python-dateutil
# pip3 install pyowm

'''
Planner Module
@class Planner
@author - Team Wizards of Coz
'''

#SET UP THE GOOGLE PROJECT FIRST AND DOWNLOAD THE CLIENT_ID JSON TO THIS FOLDER

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = '<CLIENT SECRET JSON FILE LOCATION>'
APPLICATION_NAME = '<APPLICATION_NAME>'

class Planner(WOC):
    
    cl = None
    exit_flag = False
    audioThread = None
    cubes = None
    timeRemaining = 100
    curEvent = None
    owm = None
    calendar = None
    idleAnimations = ['anim_sparking_idle_03','anim_sparking_idle_02','anim_sparking_idle_01']
    attractAttentionAnimations = ['anim_keepaway_pounce_02','reacttoblock_triestoreach_01']
    animCtr = 0
    face = None
    faceFound = False
    messageDelivered = False
    
    
    def __init__(self, *a, **kw):
        
        sys.setrecursionlimit(0x100000)
        
        cozmo.setup_basic_logging()
        cozmo.connect(self.startResponding)
        
        
        
    def startResponding(self, coz_conn):
        asyncio.set_event_loop(coz_conn._loop)
        self.coz = coz_conn.wait_for_robot()
        
        self.playIdle()
        
        self.audioThread = _thread.start_new_thread(self.startAudioThread, ())
        
        while not self.exit_flag:
            asyncio.sleep(0)
        self.coz.abort_all_actions()
    
    
    
    def accessGoogleCalendar(self):
        
        # GOOGLE CALENDAR
        self.calendar = GoogleCalendar(SCOPES,CLIENT_SECRET_FILE,APPLICATION_NAME,TZ)
        self.calendar.pollCalendar()
        event,timeToEvent = self.calendar.todaysEventAndTimeToEvent()
        
        if event is not None:
            start = event['start'].get('dateTime', event['start'].get('date'))
#             print(start)
            if timeToEvent < self.timeRemaining:
                self.coz.play_anim('anim_sparking_getin_01').wait_for_completed()
                self.findFaceAndInform(timeToEvent)
        
    
    
    def findFaceAndInform(self,timeToEvent):
        find_face = self.coz.start_behavior(cozmo.behavior.BehaviorTypes.FindFaces)
        try:
            self.face = self.coz.world.wait_for_observed_face(timeout=5)
            print("Found a face!", self.face)
            find_face.stop()
        except asyncio.TimeoutError:
            find_face.stop()
            self.coz.say_text("Look at me!",duration_scalar=1.5,voice_pitch=-1,in_parallel=True).wait_for_completed()
            self.coz.play_anim(random.choice(self.attractAttentionAnimations)).wait_for_completed()
            self.findFaceAndInform(timeToEvent)
        
        if self.faceFound == False:
            self.faceFound = True
            if self.face is not None:
                find_face.stop()
                self.coz.play_anim("anim_greeting_happy_01").wait_for_completed()
                self.coz.say_text("You have a meeting in "+str(timeToEvent)+" minutes    ! Check you calendar!",duration_scalar=2,voice_pitch=0,in_parallel=True).wait_for_completed()
                self.messageDelivered = True
                
                
     
    
    def startAudioThread(self):
        try:
            print("Take input");
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.startListening())
        except Exception as e:
            print(e)
    
    
    
    async def startListening(self):
        if self.faceFound:
            print("Taking input");
            
            r = sr.Recognizer()
            r.energy_threshold = 5000
            print(r.energy_threshold)
            with sr.Microphone(chunk_size=512) as source:
                audio = r.listen(source)
    
            try:
                speechOutput = r.recognize_google(audio)
                if self.messageDelivered == True:
                    self.processSpeech(speechOutput)
                await asyncio.sleep(1);
                await self.startListening()
    
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                await asyncio.sleep(0);
                await self.startListening()
    
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
                           
     
    def processSpeech(self,speechOutput):
        print(speechOutput)
        if 'thanks' in speechOutput or 'thank' in speechOutput:
            self.coz.play_anim("anim_greeting_happy_01").wait_for_completed()
            self.messageDelivered = False
               
    
    def playIdle(self):
        self.coz.play_anim(self.idleAnimations[self.animCtr]).wait_for_completed()
        self.animCtr += 1
        
        if self.animCtr==3:
            self.accessGoogleCalendar()
        else: 
            self.playIdle()

if __name__ == '__main__':
    Planner()