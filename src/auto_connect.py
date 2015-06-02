#! /usr/bin/python

import rospy
import subprocess
from std_msgs.msg import String
from zeroconf_msgs.msg import *

previous_list = []

def update_connection(data):
    ### TODO maybe a bad coding for adding global variable here
    global previous_list
    update_list = data.data.split(',')
    for robot in update_list:
        if robot not in previous_list:
            subprocess.call(["roslaunch", "odroid_machine","remote_zumy.launch","mname:=" + robot])
    previous_list = update_list  

if __name__ == "__main__":
    rospy.init_node('auto_connect', anonymous=True)
    rospy.Subscriber("/online_detector/online_robots", String, update_connection)
    rospy.spin()


