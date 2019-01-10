__author__ = 'Alexandre Argeris'
# Special thanks to Martin Bolduc
#
# Copyright (c) 2018 Cisco and/or its affiliates.
# This software is licensed to you under the terms of the Cisco Sample
# Code License, Version 1.0 (the "License"). You may obtain a copy of the
# License at
#                https://developer.cisco.com/docs/licenses
# All use of the material herein must be in accordance with the terms of
# the License. All rights not expressly granted by the License are
# reserved. Unless required by applicable law or agreed to separately in
# writing, software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.

import requests
import json
import sys
import re
import time
import datetime

try:
    from flask import Flask
    from flask import request
except ImportError as e:
    print(e)
    print("Looks like 'flask' library is missing.\n"
          "Type 'pip3 install flask' command to install the missing library.")
    sys.exit()

requests.packages.urllib3.disable_warnings()

# Please modify with your Bot ID token
bearer = 'BOT ID TOKEN HERE'


# Log file location and prefix 'Example : /var/log/webexteams-bot-'
log_directory = ''
log_prefix = 'webex-bot'

headers = {"Accept": "application/json", "Content-Type": "application/json; charset=utf-8", "Authorization": "Bearer " + bearer}

expected_messages = {"help me": "help",
                     "need help": "help",
                     "can you help me": "help",
                     "ayuda me": "help",
                     "help": "help",
                     "greetings": "greetings",
                     "hello": "greetings",
                     "hi": "greetings",
                     "how are you": "greetings",
                     "what's up": "greetings",
                     "what's up doc": "greetings"}

def send_spark_get(url, payload=None, js=True):
    if payload is None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js is True:
        request = request.json()
    return request

def send_spark_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request

def help_me():
    return "Sure! I can help. Below are the commands that I understand:<br/>" \
           "`help me` - I will display what I can do.<br/>" \
           "`hello` - I will display my greeting message<br/>" \
           "`info` - Send back information one this session'<br/>"

def greetings():
    return "Hi my name is {}.<br/>" \
           "Type `Help me` to see what I can do.<br/>".format(bot_name)

def info (roomType, room_title, today, timestamp, personEmail):
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')

        return "Send to Bot by: {} :<br/>" \
               "In a room type: {}<br/>" \
               "Title of the room: {} <br/>".format(personEmail, roomType, room_title)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def spark_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        #print(json.dumps(webhook, indent=4))
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')
        if (webhook['resource'] == "memberships") and (webhook['event'] == "created") and (webhook['data']['personEmail'] == bot_email):
            msg = ""
            msg = greetings()
            send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})

        elif ("@webex.bot" not in webhook['data']['personEmail']) and (webhook['resource'] == "messages"):
            result = send_spark_get('https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
            roomId_query = send_spark_get('https://api.ciscospark.com/v1/rooms/{0}'.format(webhook['data']['roomId']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower() + " ", '')
            personEmail =  result.get('personEmail', '')
            roomType = result.get('roomType', '')
            room_title = roomId_query.get('title', '')
            #print (result)
            f = open((log_directory+log_prefix+'-'+today+'.log'), "a")
            f.write(timestamp +", "+personEmail+", RoomType: " +roomType+", Room Name: "+room_title+", Command: " +in_message + '\n')
            msg = ""

            if in_message in expected_messages and expected_messages[in_message] is "help":
                msg = help_me()

            elif in_message in expected_messages and expected_messages[in_message] is "greetings":
                msg = greetings()

            elif in_message.startswith("info"):
                msg = info(roomType, room_title, today, timestamp, personEmail)

            else:
                msg = "Sorry, but I did not understand your request. Type `Help me` to see what I can do"

            if msg is not None:
                send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})

        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Spark Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Don't forget to create Webhooks to start receiving events from Cisco Spark!</i></b></center>" % bot_name
        return message

def main():
    global bot_email, bot_name
    if len(bearer) != 0:
        test_auth = send_spark_get("https://api.ciscospark.com/v1/people/me", js=False)
        if test_auth.status_code == 401:
            print("Looks like the provided access token is not correct.\n"
                  "Please review it and make sure it belongs to your bot account.\n"
                  "Do not worry if you have lost the access token. "
                  "You can always go to https://developer.ciscospark.com/apps.html "
                  "URL and generate a new access token.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName", "")
            bot_email = test_auth.get("emails", "")[0]
    else:
        print("'bearer' variable is empty! \n"
              "Please populate it with bot's access token and run the script again.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.ciscospark.com/apps.html "
              "URL and generate a new access token.")
        sys.exit()

    if "@webex.bot" not in bot_email:
        print("You have provided an access token which does not relate to a Bot Account.\n"
              "Please change for a Bot Account access toekneview it and make sure it belongs to your bot account.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.ciscospark.com/apps.html "
              "URL and generate a new access token for your Bot.")
        sys.exit()
    else:
        app.run(host='0.0.0.0', port=4980)

if __name__ == "__main__":
    main()
