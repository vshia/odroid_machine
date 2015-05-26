#!/usr/bin/env bash

export COOP_SLAM_WORKSPACE=/home/odroid/coop_slam_workspace
source $COOP_SLAM_WORKSPACE/devel/setup.bash
export ROS_HOSTNAME=$HOSTNAME.local
export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$COOP_SLAM_WORKSPACE
exec "$@"
