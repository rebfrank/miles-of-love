import argparse
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
            if activity2.startTimeGMT > self.startTimeGMT + self.duration * 0.7:
                return 0
        else:
            if self.startTimeGMT > activity2.startTimeGMT + activity2.duration * 0.7:
                return 0
        if geopy.distance.distance(self.coords, activity2.coords).miles > self.distance / 2:
            return 0
        return min(activity2.distance, self.distance)
    def __repr__(self):
        return "{0} mi on {1} ({2})".format(self.distance, self.startTimeGMT, self.id)

def getData(username):
    activities = {
        'running' : [],
        'hiking' : [],
        'cycling' : [],
        'swimming' : [],
        'uncategorized' : []
    }
    startIndex = 1
    sizeToFetch = 200
    while (True):
        r = requests.get("https://connect.garmin.com/modern/proxy/activitylist-service/activities/{0}?start={1}&limit={2}".format(username,startIndex,sizeToFetch)).json()
        if(len(r['activityList']) == 0):
            break
        startIndex += sizeToFetch
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
    return activities

def printActivity(miles, activity1, activity2, activityType):
    printsOn = True
    if printsOn:
        who = ""
        ids = ""
        date = ""
        if activity1 and activity2:
            who = "Both users"
            ids = "{0} and {1}".format(activity1.id, activity2.id)
            date = "{0} and {1}".format(activity1.startTimeGMT, activity2.startTimeGMT)
        elif activity1:
            who = "User 1"
            ids = "{0}".format(activity1.id)
            date = "{0}".format(activity1.startTimeGMT)
        elif activity2:
            who = "User 2"
            ids = "{0}".format(activity2.id)
            date = "{0}".format(activity2.startTimeGMT)
        else:
            raise ValueError("At least one activity must be provided")
        print("{0} did {1} mi on {2} ({3})".format(
            who,
            miles,
            date,
            ids,))

def countMiles(aActivities, bActivities, activityType):
    aIndex = 0
    bIndex = 0
    milesTogether = 0
    while aIndex < len(aActivities) and bIndex < len(bActivities):
        milesMatched = aActivities[aIndex].milesMatched(bActivities[bIndex])
        if milesMatched > 0:
            printActivity(milesMatched,aActivities[aIndex],bActivities[bIndex],activityType)
            milesTogether += milesMatched
            # handle case where one person recorded 2 activities for the same activity
            try:
                milesMatched = aActivities[aIndex+1].milesMatched(bActivities[bIndex])
                if milesMatched > 0:
                    printActivity(milesMatched,aActivities[aIndex+1],bActivities[bIndex],activityType)
                    milesTogether += milesMatched
                    aIndex += 1
            except IndexError:
                pass
            try:
                milesMatched = aActivities[aIndex].milesMatched(bActivities[bIndex+1])
                if milesMatched > 0:
                    printActivity(milesMatched,aActivities[aIndex],bActivities[bIndex+1],activityType)
                    milesTogether += milesMatched
                    bIndex += 1
            except IndexError:
                pass
            aIndex += 1
            bIndex += 1
        elif aActivities[aIndex].startTimeGMT > bActivities[bIndex].startTimeGMT:
            printActivity(aActivities[aIndex].distance,aActivities[aIndex],None,activityType)
            aIndex = aIndex + 1
        else:
            printActivity(bActivities[bIndex].distance,None,bActivities[bIndex],activityType)
            bIndex = bIndex + 1
    return milesTogether

parser = argparse.ArgumentParser()
parser.add_argument("user1",help="The Garmin Connect username of the first user (profile must be set to Public)")
parser.add_argument("user2",help="The Garmin Connect username of the second user (profile must be set to Public)")
args = parser.parse_args()

aActivities = getData(args.user1)
bActivities = getData(args.user2)
for activityType in aActivities.keys():
    miles = countMiles(aActivities[activityType],bActivities[activityType],activityType)
    print("\nTOTAL MILES {0} TOGETHER: {1}\n".format(activityType, miles))
