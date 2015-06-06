#! /usr/bin/python

import rospy
from zeroconf_msgs.msg import *
from zeroconf_msgs.srv import *
import nmap
import threading
from std_msgs.msg import String
import subprocess
import rosgraph.masterapi
import re

class autoConnect():
  def __init__(self):
    self.master = rosgraph.masterapi.Master('/rostopic')
    self.lock = threading.Condition()
    self.nm = nmap.PortScanner()
    self.host = 'optitrack2'
    
    self.online_robots = []
    self.lost_robots = []
    self.pdict = {}
    self.new = 0
    self.new_count = 5

    self.pub = rospy.Publisher('/online_detector/online_robots', String, queue_size=5)

  ### helper functions
  def remove_robot(self, name):
      self.online_robots.remove(name)
      rospy.loginfo(name + " is offline")
      rospy.loginfo("current online robots " + str(self.online_robots))
      if name in self.pdict:    
          self.pdict.pop(name)
    

  def add_robot(self, name):
      if name != self.host:
          self.online_robots.append(name)
          rospy.loginfo(name + " is online")
          rospy.loginfo("current online robots " + str(self.online_robots))
          p = subprocess.Popen(["roslaunch","odroid_machine","remote_zumy.launch","mname:=" + name])
          self.pdict[name] = p

  ### new connection callback
  def newCB(self, data):
      name = data.name.split()
      self.lock.acquire()
      if name[0] not in self.online_robots:
          self.add_robot(name[0])
          self.new = self.new_count
      self.lock.release()

  ### scan functions
  def online_scan(self):
      for r in self.online_robots:
          result = self.nm.scan( r+'.local', arguments='-sP')
          uphosts =  result['nmap']['scanstats']['uphosts']
          if not int(uphosts):
              self.remove_robot(r)
              self.lost_robots.append(r)

  def alive_scan(self):
      ### TODO Attention! If the zumy is accidentally power off, the heartbeat topic still can be detected!
      topics = self.master.getPublishedTopics('/')
      alive_robots = []
      for t in topics:
          m = re.search('odroid./heartBeat',str(t))
          if m != None:
              alive_robots.append(m.group(0)[:7])

      #print "alive robots:"
      #print alive_robots
      #print "online robots:"
      #print self.online_robots

      ### TODO If the host cannot hear the heartbeat from zumy. it keep relaunching remote_zumy
      for r in self.online_robots:
          if r not in alive_robots:
              p = self.pdict[r]
              p.terminate()
              p = subprocess.Popen(["roslaunch","odroid_machine","remote_zumy.launch","mname:=" + r])
              self.pdict[r] = p
    
  def lost_scan(self): 
      for r in self.lost_robots:
          result = self.nm.scan( r+'.local', arguments='-sP')
          uphosts =  result['nmap']['scanstats']['uphosts']
          if int(uphosts):
              self.add_robot(r)
              self.lost_robots.remove(r)

  ### avahi listener adding function
  def call_service(self):
      rospy.wait_for_service('/zeroconf/add_listener')
      try:
          add_listener = rospy.ServiceProxy('/zeroconf/add_listener', AddListener)
          r = add_listener('_workstation._tcp')
      except rospy.ServiceException, e:
          print "Servce call failed: %s"%e

  ### main function
  def run(self):

      rospy.init_node("onlineListener", anonymous=True)
      rospy.Subscriber("/zeroconf/new_connections", DiscoveredService, self.newCB)
      self.call_service()
      rate = rospy.Rate(1)

      print "Waiting for connection..."
      while len(self.online_robots) == 0:
          rate.sleep()

      while not rospy.is_shutdown():
          print "scanning..."
          self.lock.acquire()
          self.online_scan()
          if self.new:
              #print "####################################"
              #print self.new
              self.new = self.new - 1
          else:
              self.alive_scan()
          self.lost_scan()
          self.pub.publish(','.join(self.online_robots))
          self.lock.release()
          rate.sleep()


if __name__ == "__main__":
    print("Let's start!")
    ac = autoConnect()
    ac.run()

