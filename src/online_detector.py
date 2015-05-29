#! /usr/bin/python

import rospy
from zeroconf_msgs.msg import *
from zeroconf_msgs.srv import *
import time

online_robots = []

def lostCB(data):
    name = data.name.split()
    if name[0] in online_robots:
        online_robots.remove(name[0])
        rospy.loginfo(name[0] + " is offline")
        rospy.loginfo("current online robots " + str(online_robots))

def newCB(data):
    name = data.name.split()
    if name[0] not in online_robots:
        online_robots.append(name[0])
        rospy.loginfo(name[0] + " is online")
        rospy.loginfo("current online robots " + str(online_robots))

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
    rospy.spin()


if __name__ == "__main__":
    print("let's start!")
    listener()

