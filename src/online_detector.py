#! /usr/bin/python

import rospy
from zeroconf_msgs.msg import *
from zeroconf_msgs.srv import *
import nmap
import threading

lock = threading.Condition()
online_robots = []
nm = nmap.PortScanner()

def remove_robot(name):
    online_robots.remove(name)
    rospy.loginfo(name + " is offline")
    rospy.loginfo("current online robots " + str(online_robots))

def add_robot(name):
    online_robots.append(name)
    rospy.loginfo(name + " is online")
    rospy.loginfo("current online robots " + str(online_robots))

def lostCB(data):
    name = data.name.split()
    lock.acquire()
    if name[0] in online_robots:
        remove_robot(name[0])
    lock.release()       
  
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

def add_listener():
    rospy.wait_for_service('/zeroconf/add_listener')
    try:
        add_listener = rospy.ServiceProxy('/zeroconf/add_listener', AddListener)
        r = add_listener('_workstation._tcp')
    except rospy.ServiceException, e:
        print "Servce call failed: %s"%e

def listener():
    rospy.init_node("onlineListener", anonymous=True)
    rospy.Subscriber("/zeroconf/lost_connections", DiscoveredService, lostCB)
    rospy.Subscriber("/zeroconf/new_connections", DiscoveredService, newCB)
    add_listener()
    rate = rospy.Rate(0.5)
    while not rospy.is_shutdown():
        print "scanning..."
        nm_scan()
        rate.sleep()


if __name__ == "__main__":
    print("let's start!")
    listener()

