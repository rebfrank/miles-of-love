# TODO
# match on gps as well
# take the smaller distance of the two on matches
# retrieve the data from the public urls


import json
import requests
from datetime import datetime, timedelta

class Activity:
    def __init__(self,name,startTimeGMT,distance,duration,startLatitude,startLongitude):
        self.name = name
        self.startTimeGMT = datetime.strptime(startTimeGMT, "%Y-%m-%d %H:%M:%S")
        self.distance = distance/1609.34
        self.duration = timedelta(seconds=duration)
        self.startLatitude = startLatitude
        self.startLongitude = startLongitude
    def matches(self,activity2):
        if self.startTimeGMT < activity2.startTimeGMT:
            if activity2.startTimeGMT > self.startTimeGMT + self.duration / 2:
                return False
        else:
            if self.startTimeGMT > activity2.startTimeGMT + activity2.duration / 2:
                return False
        return True
    def __repr__(self):
        return "Name: {0}\nStart time: {1}\nDistance: {2}\n".format(self.name,
            self.startTimeGMT,
            self.distance)

def getData(username):
    r = requests.get("https://connect.garmin.com/modern/proxy/activitylist-service/activities/{0}?start=1&limit=100".format(username)).json()
    activities = {
        'running' : [],
        'hiking' : [],
        'cycling' : [],
    }
    for garminActivity in r['activityList']:
        activity = {}
        activityType = garminActivity['activityType']['typeKey']
        if activityType == 'other' and 'hike' in garminActivity['activityName'].lower():
            activityType = 'hiking'
        elif activityType == 'trail_running':
            activityType = 'running'
        elif activityType == 'mountain_biking':
            activityType = 'cycling'
        try:
            activities[activityType].append(Activity(
                garminActivity['activityName'],
                garminActivity['startTimeGMT'],
                garminActivity['distance'],
                garminActivity['duration'],
                garminActivity['startLatitude'],
                garminActivity['startLongitude']
            ))
        except KeyError:
            print("Activity type not recognized: " + activityType)
            print("Activity name: " + garminActivity['activityName'])
            exit()
    return activities

aActivities = getData("forsander")
bActivities = getData("rebfrank")
aIndex = 0
bIndex = 0
while aIndex < len(aActivities['running']) and bIndex < len(bActivities['running']):
    if aActivities['running'][aIndex].matches(bActivities['running'][bIndex]):
        print("A & B ran {0} mi together on {1}".format(
            aActivities['running'][aIndex].distance,
            aActivities['running'][aIndex].startTimeGMT))
        aIndex = aIndex + 1
        bIndex = bIndex + 1
    elif aActivities['running'][aIndex].startTimeGMT > bActivities['running'][bIndex].startTimeGMT:
        print("A ran {0} mi on {1}".format(
            aActivities['running'][aIndex].distance,
            aActivities['running'][aIndex].startTimeGMT))
        aIndex = aIndex + 1
    else:
        print("B ran {0} mi on {1}".format(
            bActivities['running'][bIndex].distance,
            bActivities['running'][bIndex].startTimeGMT))
        bIndex = bIndex + 1

