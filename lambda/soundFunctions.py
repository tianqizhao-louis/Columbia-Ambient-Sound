# This file contains functions dealing with sounds.

import json
import random
from utils import create_presigned_url

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


class SoundManager:
    def __init__(self):
        self.audios = None 
        
        with open("./documents/audios.json", "r") as file:
            self.audios = json.load(file)
    
    def get_particular_sound(self, sound_name):
        """
        This function returns the url of a particular sound
        """
        sound_name = sound_name.lower()
        url_list = []
        url_create_list=[]
        
        for index, value in enumerate(self.audios):
            if value["type"] == sound_name:
                url_list.append(value["url"])
                
        random.shuffle(url_list)
        for i in url_list:
            tem=create_presigned_url(i)
            url_create_list.append(tem)
        
        return url_create_list
        
    def get_random_sound(self):
        """
        This function randomly shuffle a sound and return back the url
        """
        if len(self.audios) == 0:
            return None
        
        audios_cp = self.audios
        random.shuffle(audios_cp)
        return create_presigned_url(audios_cp[0]["url"]), audios_cp[0]["type"]


class firestoreManager:
    def __init__(self):
        cred = credentials.Certificate('key.json')
        
        firebase_app = firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
    
    def increment_sound_stats(self, user_action):
        """
        Increment stats in firebase
        """
        sound_stats_ref = self.db.collection(u'sound_stats').document(u'%s' % user_action.lower())
        sound_stats_ref.set({
            u'freq': firestore.Increment(1)
        }, merge=True)
    
    def get_top_sound(self):
        sound_stats_ref = self.db.collection(u'sound_stats')
        query = sound_stats_ref.order_by(u'freq', direction=firestore.Query.DESCENDING).limit(1)
        results = query.stream()
        to_return = []
        
        for r in results:
            to_return.append(r.id)

        return to_return
    
    
    
    
    
    
    
    
    
    
    
    
    