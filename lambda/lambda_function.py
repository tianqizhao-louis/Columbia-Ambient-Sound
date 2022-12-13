# Sheng: 找更多的audio file，放进s3, audio.json
# Zihang: playlist feature咋弄？？
# Tianqi: customized, personalized stats


import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import logging
import ask_sdk_core.utils as ask_utils

import json
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective)

import os
import boto3
import json

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

import random

from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.dispatch_components import (AbstractRequestHandler, AbstractExceptionHandler, AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_model.interfaces.audioplayer import (
    PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata,
    StopDirective, ClearQueueDirective, ClearBehavior)

from utils import create_presigned_url

from soundFunctions import SoundManager, firestoreManager

sound_manager = SoundManager()
firestore_manager = firestoreManager()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

audio_url_list=[]


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        device_id = handler_input.request_envelope.context.system.device.device_id

        user_time_zone = ""
        greeting = ""

        try:
            user_preferences_client = handler_input.service_client_factory.get_ups_service()
            user_time_zone = user_preferences_client.get_system_time_zone(device_id)
        except Exception as e:
            user_time_zone = 'error.'
            logger.error(e)

        if user_time_zone == 'error':
            greeting = 'Hello.'
        else:
            # get the hour of the day or night in your customer's time zone
            from celebrityFunctions import get_hour
            hour = get_hour(user_time_zone)
            if 0 <= hour and hour <= 4:
                greeting = "Hi night-owl!"
            elif 5 <= hour and hour <= 11:
                greeting = "Good morning!"
            elif 12 <= hour and hour <= 17:
                greeting = "Good afternoon!"
            elif 17 <= hour and hour <= 23:
                greeting = "Good evening!"
            else:
                greeting = "Howdy partner!"


        speak_output = ''
        session_attributes = handler_input.attributes_manager.session_attributes
        session_attributes["last_intent"] = None


        if session_attributes["visits"] == 0:
            speak_output = f"{greeting} Welcome to Columbia Ambient Sound. " \
                f"Do you want to know what is the top song that is playing at Columbia?" 
        else:
            speak_output = f"{greeting} Welcome back to Columbia Ambient Sound! " \
                f"Do you want to know what is the top song that is playing at Columbia?"
        

        # increment the number of visits and save the session attributes so the
        # ResponseInterceptor will save it persistently.
        session_attributes["visits"] = session_attributes["visits"] + 1
        
        session_attributes["last_intent"] = "top_song"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


########### Tianqi ################

class UserActionIntentHandler(AbstractRequestHandler):
    """
    Handler: User Action
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_intent_name("UserActionIntent")(handler_input)
        
    def handle(self, handler_input):
        
        user_action = ask_utils.request_util.get_slot(handler_input, "action").value
        
        # write to sessions
        session_attributes = handler_input.attributes_manager.session_attributes
        session_attributes["action"] = user_action
        
        speak_output = f"You are {user_action}. Playing the sound."
        
        firestore_manager.increment_sound_stats(user_action=user_action)
        
        if user_action == "resting" :
            audio_url_list=sound_manager.get_particular_sound(sound_name="resting")
            audio_url = audio_url_list[0]
            session_attributes["url_list"] = audio_url_list
            session_attributes["current_index"]=0
            return (handler_input.response_builder.speak(speak_output)
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=audio_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                    )
            
        if user_action == "cooking" :
            audio_url_list = sound_manager.get_particular_sound(sound_name="cooking")
            audio_url=audio_url_list[0]
            session_attributes["url_list"] = audio_url_list
            session_attributes["current_index"]=0
            return (handler_input.response_builder.speak(speak_output)
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=audio_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                    )
        if user_action == "studying" :
            audio_url_list = sound_manager.get_particular_sound(sound_name="studying")
            audio_url = audio_url_list[0]
            session_attributes["url_list"] = audio_url_list
            session_attributes["current_index"]=0
            return (handler_input.response_builder.speak(speak_output)
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=audio_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                    )
        

        
class HolidayHandlerIntent(AbstractRequestHandler):
    """
    Handler: Holiday
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_intent_name("HolidayHandlerIntent")(handler_input)
        
    def handle(self, handler_input):
        
        holiday = ask_utils.request_util.get_slot(handler_input, "holiday").value
        
        # write to sessions
        session_attributes = handler_input.attributes_manager.session_attributes
        session_attributes["holiday"] = holiday
        
        speak_output = f"Enjoy the {holiday} mood! Playing the sound."
        
        firestore_manager.increment_sound_stats(user_action=holiday)
        
        if holiday == "Christmas" :
            audio_url_list = sound_manager.get_particular_sound(sound_name="christmas")
            audio_url = audio_url_list[0]
            session_attributes["url_list"] = audio_url_list
            session_attributes["current_index"]=0
            return (handler_input.response_builder.speak(speak_output)
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=audio_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                    )
            
            
        if holiday == "Halloween" :
            audio_url_list = sound_manager.get_particular_sound(sound_name="halloween")
            audio_url = audio_url_list[0]
            session_attributes["url_list"] = audio_url_list
            session_attributes["current_index"]=0
            return (handler_input.response_builder.speak(speak_output)
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=audio_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                    )
        


class ChooseModeIntent(AbstractRequestHandler):
    """
    Handler: Mode: holiday or normal
    """
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ChooseModeIntent")(handler_input)
    
    def handle(self, handler_input):
        mode = ask_utils.request_util.get_slot(handler_input, "mode").value
    
        # write to sessions
        session_attributes = handler_input.attributes_manager.session_attributes
        session_attributes["mode"] = mode
        
        if mode == "holiday":
            speak_output = f"Welcome to our special holiday mode! You can say: Christmas or Halloween."
        elif mode == "normal":
            speak_output = f"OK. What are you doing right now? You can say: studying, resting, or cooking."
        elif mode == "surprise me":
            surprise_url, surprise_mode = sound_manager.get_random_sound()
            speak_output = f"Let me surprise you! Let's be in {surprise_mode} mode!"
            firestore_manager.increment_sound_stats(user_action=surprise_mode)
            
            return (handler_input.response_builder.speak(speak_output)
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=surprise_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                    )
        
        return (handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
        )
        

###################################





########### Zihang ################

class NextIntentHandler(AbstractRequestHandler):
    """
    Handle Yes intents
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
                and ask_utils.is_intent_name("AMAZON.NextIntent")(handler_input)
        )

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        if session_attributes:

                audio_url_list = session_attributes["url_list"] 
                
                tem_index= session_attributes["current_index"]
                tem_len= len(audio_url_list)
                if tem_index == tem_len-1 :
                    tem_index=0
                else:
                    tem_index +=1
                
                session_attributes["current_index"] = int(tem_index)
                audio_url=audio_url_list[int(tem_index)]
                return (handler_input.response_builder.speak("Starting")
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=audio_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                        )
                    

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            is_intent_name("AMAZON.CancelIntent")(handler_input)
            or is_intent_name("AMAZON.StopIntent")(handler_input)
            or is_intent_name("AMAZON.PauseIntent")(handler_input)
            )
    
    def handle(self, handler_input):
        speak_output = "Goodbye!"
        return ( handler_input.response_builder
                    .speak(speak_output)
                    .add_directive(
                        ClearQueueDirective(
                            clear_behavior=ClearBehavior.CLEAR_ALL)
                        )
                    .add_directive(StopDirective())
                    .set_should_end_session(True)
                    .response
                )


class ResumeStreamIntentHandler(AbstractRequestHandler):
    def can_handle(self,handler_input):
        return (is_request_type("PlaybackController.PlayCommandIssued")(handler_input)
                or is_intent_name("AMAZON.ResumeIntent")(handler_input)
                )
    def handle(self,handler_input):
        
        return ( handler_input.response_builder
                    .add_directive(
                        PlayDirective(
                            play_behavior=PlayBehavior.REPLACE_ALL,
                            audio_item=AudioItem(
                                stream=Stream(
                                    token=stream["token"],
                                    url=stream["url"],
                                    offset_in_milliseconds=0,
                                    expected_previous_token=None),
                                metadata=stream["metadata"]
                            )
                        )
                    )
                    .set_should_end_session(True)
                    .response
                )
###################################





########### Sheng ################


###################################



class YesIntentHandler(AbstractRequestHandler):
    """
    Handle Yes intents
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
                and ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)
        )

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        if session_attributes:
            if session_attributes["last_intent"] == "top_song":
                session_attributes["last_intent"] = "play_or_not" 
                
                current_trending = firestore_manager.get_top_sound()[0]
                speak_output = f"The hottest sound trending right now is {current_trending}. Do you want me to play it?"
                
                return (handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
                )
            elif session_attributes["last_intent"] == "play_or_not":
                session_attributes["last_intent"] = None 
                current_trending = firestore_manager.get_top_sound()[0]
                firestore_manager.increment_sound_stats(user_action=current_trending)
                
                audio_url_list = sound_manager.get_particular_sound(sound_name=current_trending)
                audio_url = audio_url_list[0]
                session_attributes["url_list"] = audio_url_list
                session_attributes["current_index"]=0
                return (handler_input.response_builder.speak("Starting")
                                                  .add_directive(PlayDirective(play_behavior=PlayBehavior.REPLACE_ALL,
                                                                               audio_item=AudioItem(stream=Stream(token=1,
                                                                                                                  url=audio_url,
                                                                                                                  offset_in_milliseconds=0,
                                                                                                                  expected_previous_token=None))))
                                                  .set_should_end_session(True)
                                                  .response
                        )
                    
                

class NoIntentHandler(AbstractRequestHandler):
    """
    Handle No intents
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return (
            ask_utils.is_request_type("IntentRequest")(handler_input)
                and ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input)
        )

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        if session_attributes:
            if session_attributes["last_intent"] == "top_song" or session_attributes["last_intent"] == "play_or_not":
                session_attributes["last_intent"] = None 
                speak_output = "Okay, You can choose to play the sound in a holiday mode or normal mode. Or, you can say surprise me! Which one do you like?"
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(speak_output)
                        .response
                )


# class GetBirthdayIntentHandler(AbstractRequestHandler):
#     """Handler for Skill Launch."""
#     def can_handle(self, handler_input):
#         # type: (HandlerInput) -> bool

#         return (
#             ask_utils.is_request_type("IntentRequest")(handler_input)
#                 and ask_utils.is_intent_name("GetBirthdayIntent")(handler_input)
#         )

#     def handle(self, handler_input):
#         # type: (HandlerInput) -> Response
#         speak_output = ''

#         # get the current session attributes, creating an object you can read/update
#         session_attributes = handler_input.attributes_manager.session_attributes

#         # if there's a current_celeb attribute but it's empty, or there isn't one
#         # error, cue them to say "yes" and end

#         if session_attributes["current_celeb"] == None:

#             speak_output = "I'm sorry, there's no active question right now. Would you like a question?"

#             return (
#                 handler_input.response_builder
#                     .speak(speak_output)
#                     .ask(speak_output)
#                     .response
#             )

#         # Get the slot values
#         year = ask_utils.request_util.get_slot(handler_input, "year").value
#         month = ask_utils.request_util.get_slot(handler_input, "month").value

#         # Okay, check the answer
#         from celebrityFunctions import check_answer
#         winner = check_answer(
#             session_attributes["current_celeb"],
#             month,
#             year
#         )

#         # Add the celebrity to the list of past celebs.
#         # Store the value for the rest of the function,
#         # and set the current celebrity to empty
#         session_attributes["past_celebs"].append(session_attributes["current_celeb"])
#         cname = session_attributes["current_celeb"]["name"]
#         session_attributes["current_celeb"] = None

#         # We'll need variables for our visual. Let's initialize them.
#         title = ''
#         subtitle = ''

#         # Did they get it?
#         if winner:
#             session_attributes["score"] = session_attributes["score"] + 1
#             title = 'Congratulations!'
#             subtitle = 'Wanna go again?'
#             speak_output = f"Yay! You got ${cname}'s birthday right! Your score is now " \
#                 f"{session_attributes['score']}. Want to try another?"
#         else:
#             title = 'Awww shucks'
#             subtitle = 'Another?'
#             speak_output = f"Sorry. You didn't get the right month and year for " \
#                 f"{cname}. Maybe you'll get the next one. Want to try another?"

#         # store all the updated session data
#         handler_input.attributes_manager.session_attributes = session_attributes

#         #====================================================================
#         # Add a visual with Alexa Layouts
#         #====================================================================

#         # Import an Alexa Presentation Language (APL) template
#         with open("./documents/APL_simple.json") as apl_doc:
#             apl_simple = json.load(apl_doc)

#             if ask_utils.get_supported_interfaces(
#                     handler_input).alexa_presentation_apl is not None:
#                 handler_input.response_builder.add_directive(
#                     RenderDocumentDirective(
#                         document=apl_simple,
#                         datasources={
#                             "myData": {
#                                 #====================================================================
#                                 # Set a headline and subhead to display on the screen if there is one
#                                 #====================================================================
#                                 "Title": title,
#                                 "Subtitle": subtitle,
#                             }
#                         }
#                     )
#                 )

#         return (
#             handler_input.response_builder
#                 .speak(speak_output)
#                 .ask(speak_output)
#                 .response
#         )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hello World!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


# '''
# class CancelOrStopIntentHandler(AbstractRequestHandler):
#     """Single handler for Cancel and Stop Intent."""
#     def can_handle(self, handler_input):
#         # type: (HandlerInput) -> bool
#         return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
#                 ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

#     def handle(self, handler_input):
#         # type: (HandlerInput) -> Response
#         speak_output = "Goodbye!"

#         return (
#             handler_input.response_builder
#                 .speak(speak_output)
#                 .response
#         )
# '''

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class LoadDataInterceptor(AbstractRequestInterceptor):
    """Check if user is invoking skill for first time and initialize preset."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        session_attributes = handler_input.attributes_manager.session_attributes

        # ensure important variables are initialized so they're used more easily in handlers.
        # This makes sure they're ready to go and makes the handler code a little more readable
        # if 'current_celeb' not in session_attributes:
        #     session_attributes["current_celeb"] = None

        # if 'score' not in session_attributes:
        #     session_attributes["score"] = 0

        # if 'past_celebs' not in persistent_attributes:
        #     persistent_attributes["past_celebs"] = []

        # if 'past_celebs' not in session_attributes:
        #     session_attributes["past_celebs"] = []

        # if you're tracking past_celebs between sessions, use the persistent value
        # set the visits value (either 0 for new, or the persistent value)
        # session_attributes["past_celebs"] = persistent_attributes["past_celebs"] if CELEB_TRACKING else session_attributes["past_celebs"]
        session_attributes["visits"] = persistent_attributes["visits"] if 'visits' in persistent_attributes else 0
        session_attributes["url_list"] = persistent_attributes["url_list"] if 'url_list' in persistent_attributes else []
        session_attributes["current_index"] = persistent_attributes["current_index"] if 'current_index' in persistent_attributes else 0


class LoggingRequestInterceptor(AbstractRequestInterceptor):
    """Log the alexa requests."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug('----- REQUEST -----')
        logger.debug("{}".format(
            handler_input.request_envelope.request))


class SaveDataInterceptor(AbstractResponseInterceptor):
    """Save persistence attributes before sending response to user."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        session_attributes = handler_input.attributes_manager.session_attributes

        # persistent_attributes["past_celebs"] = session_attributes["past_celebs"] if CELEB_TRACKING  else []
        persistent_attributes["visits"] = session_attributes["visits"]
        persistent_attributes["url_list"] =session_attributes["url_list"] 
        persistent_attributes["current_index"] =session_attributes["current_index"] 

        handler_input.attributes_manager.save_persistent_attributes()

class LoggingResponseInterceptor(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug('----- RESPONSE -----')
        logger.debug("{}".format(response))



# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = StandardSkillBuilder(
    table_name=os.environ.get("DYNAMODB_PERSISTENCE_TABLE_NAME"), auto_create_table=False)
##
#sb.add_request_handler(CheckAudioInterfaceHandler())
##
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(UserActionIntentHandler())
sb.add_request_handler(HolidayHandlerIntent())
sb.add_request_handler(ChooseModeIntent())
sb.add_request_handler(ResumeStreamIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler()) 
sb.add_request_handler(NextIntentHandler())
# sb.add_request_handler(GetBirthdayIntentHandler())
# sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
#sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

# Interceptors
sb.add_global_request_interceptor(LoadDataInterceptor())
sb.add_global_request_interceptor(LoggingRequestInterceptor())

sb.add_global_response_interceptor(SaveDataInterceptor())
sb.add_global_response_interceptor(LoggingResponseInterceptor())

lambda_handler = sb.lambda_handler()









##3
# This handler checks if the device supports audio playback
# '''
# class CheckAudioInterfaceHandler(AbstractRequestHandler):

#     def can_handle(self, handler_input):
#         if handler_input.request_envelope.context.system.device:
#             return handler_input.request_envelope.context.system.device.supported_interfaces.audio_player is None
#         else:
#             return False

#     def handle(self, handler_input):
#         language_prompts = handler_input.attributes_manager.request_attributes["_"]
#         speech_output = language_prompts["DEVICE_NOT_SUPPORTED"]
        
#         return (
#             handler_input.response_builder
#                 .speak(speech_output)
#                 .set_should_end_session(True)
#                 .response
#             )
# ##
# '''