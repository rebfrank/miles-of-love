import requests
import geopy.distance
from datetime import datetime, timedelta

class Activity:
    def __init__(self,name,startTimeGMT,distance,duration,startLatitude,startLongitude,gid):
        self.name = name
        self.startTimeGMT = datetime.strptime(startTimeGMT, "%Y-%m-%d %H:%M:%S")
        self.distance = distance/1609.34
        self.duration = timedelta(seconds=duration)
        self.coords = (startLatitude, startLongitude)
        self.id = gid
    def milesMatched(self,activity2):
        if self.startTimeGMT < activity2.startTimeGMT:
            if activity2.startTimeGMT > self.startTimeGMT + self.duration / 2:
                return 0
        else:
            if self.startTimeGMT > activity2.startTimeGMT + activity2.duration / 2:
                return 0
        if geopy.distance.distance(self.coords, activity2.coords).miles > self.distance / 2:
            return 0
        return min(activity2.distance, self.distance)
    def __repr__(self):
        return "{0} mi on {1} ({2})".format(self.distance, self.startTimeGMT, self.id)

def getData(username):
    r = requests.get("https://connect.garmin.com/modern/proxy/activitylist-service/activities/{0}?start=1&limit=2000".format(username)).json()
    activities = {
        'running' : [],
        'hiking' : [],
        'cycling' : [],
        'swimming' : [],
        'uncategorized' : []
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
        'resort_skiing_snowboarding_ws' : 'uncategorized',
        'transition' : 'uncategorized',
        'whitewater_rafting_kayaking' : 'uncategorized',
        'road_biking' : 'cycling',
        'treadmill_running' : 'running',
        'multi_sport' : 'uncategorized',
    }
    for garminActivity in r['activityList']:
        activityType = garminActivity['activityType']['typeKey']
        if activityType == 'other':
            if 'hike' in garminActivity['activityName'].lower():
                activityType = 'hiking'
            elif 'walking' in garminActivity['activityName'].lower():
                activityType = 'hiking'
            elif 'running' in garminActivity['activityName'].lower():
                activityType = 'running'
            elif 'austin' in garminActivity['activityName'].lower():
                activityType = 'running'
            elif 'denver' in garminActivity['activityName'].lower():
                activityType = 'running'
            # filter out skiing by checking elevation and max speed
            elif garminActivity['elevationGain'] < 2100:
                # garmin speeds are in m/s
                if garminActivity['maxSpeed'] and garminActivity['maxSpeed'] < 11:
                    if garminActivity['averageSpeed'] < 0.8904:
                        activityType = 'hiking'
                    elif garminActivity['averageSpeed'] < 3.3528:
                        activityType = 'running'
                    if garminActivity['elevationGain'] > 900:
                        print("Guessed as run or hike: {0}".format(garminActivity['activityId']))
        try:
            activityType = activityTypeMapping[activityType]
            activities[activityType].append(Activity(
                garminActivity['activityName'],
                garminActivity['startTimeGMT'],
                garminActivity['distance'],
                garminActivity['duration'],
                garminActivity['startLatitude'],
                garminActivity['startLongitude'],
                garminActivity['activityId']
            ))
        except KeyError:
            print("Activity type not recognized: {0}, {1} ({2})".format(
                activityType,
                garminActivity['activityName'],
                garminActivity['activityId']))
            #exit()
    return activities

def printActivity(who, activity, activityType):
    printsOn = False
    if printsOn:
        print("{0} did {1} {2}".format(
            who,
            activity,
            activityType))

def countMiles(aActivities, bActivities, activityType):
    aIndex = 0
    bIndex = 0
    milesTogether = 0
    while aIndex < len(aActivities) and bIndex < len(bActivities):
        milesMatched = aActivities[aIndex].milesMatched(bActivities[bIndex])
        if milesMatched > 0:
            printActivity("A & B",aActivities[aIndex],activityType)
            milesTogether += milesMatched
            aIndex = aIndex + 1
            bIndex = bIndex + 1
        elif aActivities[aIndex].startTimeGMT > bActivities[bIndex].startTimeGMT:
            printActivity("A",aActivities[aIndex],activityType)
            aIndex = aIndex + 1
        else:
            printActivity("B",bActivities[bIndex],activityType)
            bIndex = bIndex + 1
    return milesTogether

aActivities = getData("forsander")
bActivities = getData("rebfrank")
for activityType in aActivities.keys():
    miles = countMiles(aActivities[activityType],bActivities[activityType],activityType)
    print("\n\nTOTAL MILES {0} TOGETHER: {1}".format(activityType, miles))
