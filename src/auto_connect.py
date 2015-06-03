#! /usr/bin/python

import rospy
from zeroconf_msgs.msg import *
from zeroconf_msgs.srv import *
import nmap
import threading
from std_msgs.msg import String
import subprocess

lock = threading.Condition()
online_robots = []
pdict = {}
nm = nmap.PortScanner()
host = 'optitrack2'

list_pub = rospy.Publisher('/online_detector/online_robots', String, queue_size=5)

def remove_robot(name):
    online_robots.remove(name)
    rospy.loginfo(name + " is offline")
    rospy.loginfo("current online robots " + str(online_robots))
    list_pub.publish(','.join(online_robots))
    if name in pdict:    
        pdict.pop(name)
    

def add_robot(name):
    if name != host:
        online_robots.append(name)
        rospy.loginfo(name + " is online")
        rospy.loginfo("current online robots " + str(online_robots))
        list_pub.publish(','.join(online_robots))
        p = subprocess.Popen(["roslaunch","odroid_machine","remote_zumy.launch","mname:=" + name])
        pdict[name] = p.pid

def newCB(data):
    name = data.name.split()
    lock.acquire()
    if name[0] not in online_robots:
        add_robot(name[0])
    lock.release()

def nm_scan():
    lock.acquire()
    for r in online_robots:
        result = nm.scan( r+'.local', arguments='-sP')
        uphosts =  result['nmap']['scanstats']['uphosts']
        if not int(uphosts):
            remove_robot(r)
    lock.release()

def call_service():
    rospy.wait_for_service('/zeroconf/add_listener')
    try:
        add_listener = rospy.ServiceProxy('/zeroconf/add_listener', AddListener)
        r = add_listener('_workstation._tcp')
    except rospy.ServiceException, e:
        print "Servce call failed: %s"%e

def run():
    rospy.init_node("onlineListener", anonymous=True)
    rospy.Subscriber("/zeroconf/new_connections", DiscoveredService, newCB)
    call_service()
    rate = rospy.Rate(0.5)

    while len(online_robots) == 0:
        print "waiting for connections"
        rate.sleep()

    while not rospy.is_shutdown():
        print "scanning..."
        nm_scan()
        rate.sleep()


if __name__ == "__main__":
    print("Let's start!")
    run()

