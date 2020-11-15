from random import randint
import sys, traceback, threading, socket
import imageio
import numpy as np
from datetime import datetime
from VideoStream import VideoStream
from RtpPacket import RtpPacket
class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	FORWARD = 'FORWARD'
	BACKWARD = 'BACKWARD'
	DESCRIBE = 'DESCRIBE'
	GETLIST = 'GETLIST'
	
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCH = 3
	state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
	
	clientInfo = {}
	videoListName = []


	def __init__(self, clientInfo):
		self.clientInfo = clientInfo
		
	def run(self):
		new_t = threading.Thread(target=self.recvRtspRequest)
		new_t.start()

	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(256)
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))
	
	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# Get the request type
		request = data.split('\n')
		line1 = request[0].split(' ')
		requestType = line1[0]
		
		# Get the media file name
		filename = line1[1]
		
		# Get the RTSP sequence number 
		seq = request[1].split(' ')

		# Process SETUP request
		print(requestType)
		if requestType == self.SETUP:
			if self.state == self.INIT:
				# Update state
				print("processing SETUP\n")
				try:
					#print(filename)
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.state = self.READY
					self.clientInfo['videoStream'].totalFrame(filename)
					
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
				
				# Generate a randomized RTSP session ID
				self.clientInfo['session'] = randint(100000, 999999)
				# Send RTSP reply
				self.replyRtsp(self.OK_200, seq[1])
				totalTime = ("tt" + ' ' + str(self.clientInfo['videoStream'].totalTime()) + ' ' + str(self.clientInfo['videoStream'].getFPS())).encode()
				self.clientInfo['rtspSocket'][0].send(totalTime)
				# Get the RTP/UDP port from the last line

				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
		
		# Process PLAY request 		
		elif requestType == self.PLAY:
			if self.state == self.READY or self.state == self.SWITCH:
				print("processing PLAY\n")
				self.state = self.PLAYING
				
				# Create a new socket for RTP/UDP
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				self.replyRtsp(self.OK_200, seq[1])

				# Create a new thread and start sending RTP packets
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker'] = threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()
		
		# Process PAUSE request
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
			
				self.replyRtsp(self.OK_200, seq[1])
			
		# Process TEARDOWN request
		elif requestType == self.TEARDOWN:
				print("processing TEARDOWN\n")
				try:
					self.clientInfo['event'].set()
				except: pass
				self.state = self.INIT
				self.replyRtsp(self.OK_200, seq[1])
				# Close the RTP socket
				try:
					self.clientInfo['rtpSocket'].close()
				except: pass
		
		# Process FORWARD request
		elif requestType == self.FORWARD:
			if self.state == self.PLAYING or self.state == self.READY:
				print("processing FORWARD\n")
				self.clientInfo['videoStream'].moveForward()
				self.replyRtsp(self.OK_200, seq[1])

		# Process BACKWARDvrequest
		elif requestType == self.BACKWARD:
			if self.state == self.PLAYING or self.state == self.READY:
				print("processing BACKWARD\n")
				self.clientInfo['videoStream'].moveBackward()
				self.replyRtsp(self.OK_200, seq[1])
		elif requestType == self.DESCRIBE:
				print("processing DESCRIBE\n")
				self.replyRtsp(self.OK_200, seq[1])
				
				v = 0 #protocol version
				s = 'Video streaming by using RTP and RTSP protocol'
				t = datetime.now()
				m = 'video ' + str(self.clientInfo['rtpPort']) + ' RTP/UDP'
				a = 'control:streamid=' + str(self.clientInfo['session']) + '\na=mimetype:string;\"video/MJPEG\"'
				sdp1 ='\n\nv=' + str(v) + '\ns=' + s + '\nt=' + str(t) +'\nm=' + m + '\na=' + a
				sdp = 'cc' + 'Content-Base:' + filename + '\nContent-Type:application/sdp' + '\nContent-Length:' + str(len(sdp1)) + sdp1
				self.clientInfo['rtspSocket'][0].send(sdp.encode())				  
		elif requestType == self.GETLIST:
				try:
					self.clientInfo['event'].set()
				except: pass
				self.state = self.SWITCH
				print("processing GETLIST\n")
				jsonFile = open("videoList.txt","r")
				output = ''
				for line in jsonFile.readlines():
					output += line
				reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq[1] + '\nSession: ' + str(self.clientInfo['session']) + '\n' + output
				connSocket = self.clientInfo['rtspSocket'][0] ## because this is RTSP/TCP, unlike the rpt sender,
				connSocket.send(reply.encode())
			
	def sendRtp(self):
		"""Send RTP packets over UDP."""
		while True:
			t = 1/self.clientInfo['videoStream'].getFPS()
			self.clientInfo['event'].wait(t) 
			
			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet(): 
				break 
				
			data = self.clientInfo['videoStream'].nextFrame()
			if data: 
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port)) #UDP
				except:
					print("Connection Error")

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			connSocket = self.clientInfo['rtspSocket'][0] ## because this is RTSP/TCP, unlike the rpt sender,
			connSocket.send(reply.encode())					## which uses RTP/UDP	
		
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")
