# TODO
# match on gps as well
# take the smaller distance of the two on matches

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
    r = requests.get("https://connect.garmin.com/modern/proxy/activitylist-service/activities/{0}?start=1&limit=2000".format(username)).json()
    activities = {
        'running' : [],
        'hiking' : [],
        'cycling' : [],
        'swimming' : [],
        'skiing' : []
    }
    activityTypeMapping = {
        'running' : 'running',
        'hiking' : 'hiking',
        'cycling' : 'cycling',
        'trail_running' : 'running',
        'mountain_biking' : 'cycling',
        'walking' : 'hiking',
        'open_water_swimming' : 'swimming',
        'lap_swimming' : 'swimming',
        'resort_skiing_snowboarding_ws' : 'skiing',
        'road_biking' : 'cycling',
    }
    for garminActivity in r['activityList']:
        activityType = garminActivity['activityType']['typeKey']
        if activityType == 'other':
            if 'hike' in garminActivity['activityName'].lower():
                activityType = 'hiking'
            elif 'monterosso al mare' in garminActivity['activityName'].lower():
                activityType = 'hiking'
            elif 'walking' in garminActivity['activityName'].lower():
                activityType = 'hiking'
            elif 'running' in garminActivity['activityName'].lower():
                activityType = 'running'
            elif 'austin' in garminActivity['activityName'].lower():
                activityType = 'running'
            elif 'denver' in garminActivity['activityName'].lower():
                activityType = 'running'
        try:
            activityType = activityTypeMapping[activityType]
            activities[activityType].append(Activity(
                garminActivity['activityName'],
                garminActivity['startTimeGMT'],
                garminActivity['distance'],
                garminActivity['duration'],
                garminActivity['startLatitude'],
                garminActivity['startLongitude']
            ))
        except KeyError:
            print("Activity type not recognized: {0}, {1} ({2})".format(
                activityType,
                garminActivity['activityName'],
                garminActivity['activityId']))
            #exit()
    return activities

aActivities = getData("forsander")
bActivities = getData("rebfrank")
aIndex = 0
bIndex = 0
milesTogether = 0
while aIndex < len(aActivities['running']) and bIndex < len(bActivities['running']):
    if aActivities['running'][aIndex].matches(bActivities['running'][bIndex]):
        print("A & B ran {0} mi together on {1}".format(
            aActivities['running'][aIndex].distance,
            aActivities['running'][aIndex].startTimeGMT))
        milesTogether += aActivities['running'][aIndex].distance
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
print("\n\nTOTAL MILES TOGETHER: {0}".format(milesTogether))
