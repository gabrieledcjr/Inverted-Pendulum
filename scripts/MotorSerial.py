#!/usr/bin/env python

"""
Author: Brandon Kallaher (brandon.kallaher@wsu.edu)
Description:
	Subcribes to /cmd for controlling the motor
	Publishes to /motor/info to send out Debug information from the motor
"""

import rospy
import serial
import sys
import os.path
import threading


#import our messages
from inverted_pendulum.msg import Cmd
from inverted_pendulum.msg import MotorInfo
from std_msgs.msg import Header

#define variables for changing later
port = '/dev/ttyACM0'

class Timeout:
	def __init__(self, timeout_period):
		self.timeout_duration = rospy.Duration.from_sec(timeout_period)
		self.time_expire = rospy.Time.now() + self.timeout_duration

	def reset(self):
		self.time_expire = rospy.Time.now() + self.timeout_duration

	def isExpired(self):
		return rospy.Time.now() > self.time_expire


class Motor():
	def __init__(self, Port='/dev/ttyACM0', baudrate=115200):
		self.ser = serial.Serial()
		self.ser.timeout = 1
		self.ser.baudrate = baudrate
		self.ser.port = Port
		self.ser.open()
		self.timer = Timeout(2)

		self.update_period = .5

		self.error_codes = 0
		self.supply_voltage = 0
		self.temperature = 0
		self.speed = 0
		self.lock = threading.Lock()

	def __del__(self):
		self.Stop()
		self.ser.close()

	def callback(self, data):
		cmd = data.cmd
		if cmd > 0:
			cmd = min(100, cmd)
			self.MoveRight(cmd)
		elif cmd < 0:
			cmd = max(-100, cmd)
			self.MoveLeft(abs(cmd))
		elif cmd == 0:
			self.Stop()

		self.timer.reset()


	def MoveRight(self, percent):
		self.Enable()
		speed = self.getValueFromPercent(percent)
		speed1 = chr(speed & 0x1F)
		speed2 = chr(speed >> 5)
		self.lock.acquire()
		try:
			self.ser.write(chr(0x85) + speed1 + speed2)
		finally:
			self.lock.release()


	def MoveLeft(self, percent):
		self.Enable()
		speed = self.getValueFromPercent(percent)
		speed1 = chr(speed & 0x1F)
		speed2 = chr(speed >> 5)
		self.lock.acquire()
		try:
			self.ser.write(chr(0x86) + speed1 + speed2)
		finally:
			self.lock.release()

	def Stop(self):
		self.lock.acquire()
		try:
			self.ser.write(chr(0x92))
			self.ser.write(chr(32))
		finally:
			self.lock.release()
	
	def Enable(self):
		self.lock.acquire()
		try:
			self.ser.write(chr(0x83))
		finally:
			self.lock.release()

	@staticmethod
	def getValueFromPercent(percent):
		return int(3200 * percent / 100)

	def ReadVar(self, addr):
		self.lock.acquire()
		try:
			self.ser.flushInput()
			self.ser.write(chr(0xA1) + chr(addr))
			[lbyte, hbyte] = self.ser.read(2)
		finally:
			self.lock.release()

		result = (ord(hbyte) << 8) | ord(lbyte)
		return result

def signed16(val):
	if(val & 0x8000): #if val is negative
		return -((~val & 0xEFFF) + 1)
	else:
		return val

	

if __name__ == '__main__':
	#initialize the ros node
	rospy.init_node('MotorSerial')

	motor = Motor()

	#Setup the publisher and subscriber
	sub = rospy.Subscriber('cmd', Cmd, motor.callback)
	pub = rospy.Publisher('motor/info', MotorInfo, queue_size=1)

	r = rospy.Rate(10)

	#check to make sure the port actually exists
	"""
	if not os.path.isfile(port):
		print "The serial port {} could not be opened!\n".format(port)
		#sys.exit(1)
	"""




	#Send the Safe Start command upon boot
	motor.Enable()

	while not rospy.is_shutdown():
		rospy.logdebug("starting read")
		motor_info = MotorInfo()
		motor_info.header = Header()
		motor_info.header.stamp = rospy.Time.now()
		motor_info.errorStatus = motor.ReadVar(1)
		motor_info.SerialError  = motor.ReadVar(2) 
		motor_info.limitStatus = motor.ReadVar(3)
		motor_info.targetSpeed = signed16(motor.ReadVar(20))
		motor_info.speed = signed16(motor.ReadVar(21))
		motor_info.brakeAmt = motor.ReadVar(22)
		motor_info.vin = motor.ReadVar(23)/1000
		motor_info.temp = motor.ReadVar(24)/10
		rospy.logdebug("finished read")

		pub.publish(motor_info)
		
		if motor.timer.isExpired():
			motor.Stop()
		
		r.sleep() 

	#stop the motor
	motor.Stop()
