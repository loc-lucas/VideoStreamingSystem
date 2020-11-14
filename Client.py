from socket import timeout
from threading import Thread, current_thread
from PySide2.QtWidgets import QWidget,QPushButton, QMessageBox, QLabel
from PySide2.QtWidgets import QApplication, QSlider, QVBoxLayout, QHBoxLayout
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtCore import Qt,QSize
from time import time
from PIL import Image
import socket, threading, sys, traceback, os
import imageio
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

	
class Client(QWidget):
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	#startTime = 0
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	FORWARD = 4
	BACKKWARD = 5
	DESCRIBE = 6
	GETLIST = 7
	
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		super(Client, self).__init__()
		self.master = master
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.stopListeningAcked = 0
		self.connectToServer()
		self.openRtpPort()
		# self.getListOfVids()
		self.frameNbr = 0
		self.totalTime = 0
		self.replySent = 0

		self.setWindowTitle("Promise")
		self.label = QLabel(self)
		self.label.setFixedSize(800,450)
		self.label.setStyleSheet("QWidget {background-color: rgba(0,0,0,1);}")
		self.label.setAlignment(Qt.AlignCenter)
		self.setGeometry(400,300,800,550)
		self.init_ui()

	def init_ui(self):
		#Apps icon
		appIcon = QIcon("image.icon")
		self.setWindowIcon(appIcon)
		#Create slider
		slider = QSlider(Qt.Horizontal)
		slider.setRange(0,self.frameNbr)
		#Create buttons
		playBtn = QPushButton("", self)
		playBtn.setFixedWidth(150)
		playBtn.setIconSize(QSize(30,30))
		playBtn.setIcon(QIcon('play.icon'))
		playBtn.clicked.connect(self.playMovie)
		
		pauseBtn = QPushButton("", self)
		pauseBtn.setFixedWidth(150)
		pauseBtn.setIconSize(QSize(30,30))
		pauseBtn.setIcon(QIcon('pause.icon'))
		pauseBtn.clicked.connect(self.pauseMovie)


		stopBtn = QPushButton("", self)
		stopBtn.setFixedWidth(150)
		stopBtn.setIcon(QIcon('stop.icon'))
		stopBtn.setIconSize(QSize(30,30))
		stopBtn.clicked.connect(self.stopMovie)

		bwBtn = QPushButton("", self)
		bwBtn.setFixedWidth(150)
		bwBtn.setIcon(QIcon('backward.icon'))
		bwBtn.setIconSize(QSize(30,30))
		bwBtn.clicked.connect(self.bwMovie)

		fwBtn = QPushButton("", self)
		fwBtn.setFixedWidth(150)
		fwBtn.setIcon(QIcon('forward.icon'))
		fwBtn.setIconSize(QSize(30,30))
		fwBtn.clicked.connect(self.fwMovie)

		# brBtn = QPushButton("", self)			## print video rate
		# brBtn.setFixedWidth(150)
		# brBtn.setIcon(QIcon('forward.icon'))
		# brBtn.setIconSize(QSize(30,30))
		# brBtn.clicked.connect(self.videoRate)

		# plBtn = QPushButton("", self)				## print packet loss rate
		# plBtn.setFixedWidth(150)
		# plBtn.setIcon(QIcon('forward.icon'))
		# plBtn.setIconSize(QSize(30,30))
		# plBtn.clicked.connect(self.rtpLossRate)
		infoBtn = QPushButton("", self)
		infoBtn.setFixedWidth(150)
		infoBtn.setIcon(QIcon('info.icon'))
		infoBtn.setIconSize(QSize(30,30))
		infoBtn.clicked.connect(self.describeMovie)
		#HBoxLayout
		hBox = QHBoxLayout()
		hBox.setContentsMargins(0,0,0,0)
		hBox.addWidget(infoBtn)
		hBox.addWidget(bwBtn)
		hBox.addWidget(playBtn)
		hBox.addWidget(fwBtn)
		hBox.addWidget(pauseBtn)
		hBox.addWidget(stopBtn)
		# hBox.addWidget(brBtn)
		# hBox.addWidget(plBtn)
		#VBoxLayout
		vBox = QVBoxLayout()
		vBox.addWidget(self.label)
		vBox.addWidget(slider)
		vBox.addLayout(hBox)	
		vBox.addStretch()
		self.setLayout(vBox)

	# def getListOfVids(self):
	# 	self.sendRtspRequest(self.GETLIST)

	def bwMovie(self):
		if self.state == self.PLAYING or self.state == self.READY:
			self.sendRtspRequest(self.BACKKWARD)
	def fwMovie(self):
		if self.state == self.PLAYING or self.state == self.READY:
			self.sendRtspRequest(self.FORWARD)
	def describeMovie(self):
		self.sendRtspRequest(self.DESCRIBE)
	def closeEvent(self, event):
		reply = QMessageBox.question(
			self,
			self.tr("Confirmation"),
			self.tr("You are about to quit!"),
			QMessageBox.Yes|
			QMessageBox.No, QMessageBox.No)
		if reply == QMessageBox.Yes:
			self.exitClient()
			event.accept()
		else:
			event.ignore()
		

	def stopMovie(self):
		if (self.requestSent == self.PAUSE and self.state == self.READY) or self.requestSent == self.PLAY:
			self.sendRtspRequest(self.TEARDOWN)
			self.play_t.join()
			self.recvRtsp_t.join()
			self.rtspSeq = 0
			self.sessionId = 0
			self.requestSent = -1
			self.stopListeningAcked = 0
			self.frameNbr = 0	
			self.label.clear()
			self.sendRtspRequest(self.SETUP)

	def exitClient(self):
		"""Teardown button handler."""
		#TODO
		self.sendRtspRequest(self.TEARDOWN)
		if self.state == self.READY and self.requestSent == self.PAUSE:
			self.play_t.join()
		self.recvRtsp_t.join()
		self.rtspSocket.shutdown(socket.SHUT_RDWR)
		self.rtspSocket.close()
		self.rtpSocket.shutdown(socket.SHUT_RDWR)
		self.rtpSocket.close()
		self.master.quit() ### close the GUI window

	def pauseMovie(self):
		"""Pause button handler."""
		#TODO
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
			self.duration += round(float(time()),2) - self.startTime ## calculate total duration
			self.startTime = 0	#set start time of the duration to 0
			#self.stopListeningAcked = 1
			self.play_t.join()	
			
	
	def playMovie(self):
		"""Play button handler."""
		#TODO
		#if self.firstPlay == 0:
		if self.state == self.READY:
			self.startTime = round(float(time()),2)	#set start time of the duration when press PLAY
			self.sendRtspRequest(self.PLAY)
			self.play_t = threading.Thread(target = self.listenRtp)
			self.play_t.start()
	
	def videoRate(self):
		"""calculate video rate (bit/s)"""
		#videoSize = 1 ##  take from the description
		if self.duration == 0:
			self.duration = self.videoDuration
			bitRate = round(float(self.playedSize) / self.duration, 2)
		else:
			bitRate = round(float(self.playedSize) / self.duration, 2)
		return bitRate

	def rtpLossRate(self, totalPacket):
		"""calculate RTP packet loss rate"""
		totalPacket = 1
		lossRate = self.packetLoss / totalPacket
		# print(self.packetLoss)
		return lossRate

	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		while True:
			#print("ack = ", self.stopListeningAcked)
			try:
				#print(threading.active_count())
				data = self.rtpSocket.recv(40960)   ## Why 20480?
				if data:
					
					rtpPacket = RtpPacket() 		## In reality, is the RtpPacket.py the same place as Client.py?
					rtpPacket.decode(data)
					current_frame = rtpPacket.seqNum()
					if current_frame - self.frameNbr > 1 :
						self.packetLoss += current_frame - self.frameNbr - 1
					self.videoDuration = round(float(time()),2) - self.startTime - 0.05*2		#calculate  video duration
					#print(self.videoDuration)
					if current_frame > self.frameNbr:
						self.frameNbr = current_frame
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				if self.stopListeningAcked == 1:
					break
				
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		#TODO

		file_name = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		temp_file = open(file_name, 'wb') ## open in binary format and write
		temp_file.write(data)
		temp_file.close()
		#imageio.imwrite(file_name, np.array(data[3:]).reshape(data[0],data[1],3))
		self.playedSize += os.path.getsize(file_name)	## total played video size
		return file_name

	def updateMovie(self, imageFile):
		self.pixmap = QPixmap(imageFile)
		w = self.label.width()
		h = self.label.height()
		self.label.setPixmap(self.pixmap.scaled(w, h, Qt.KeepAspectRatio))

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		#TODO
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
			self.sendRtspRequest(self.SETUP)
		except:
			QMessageBox.warning(self,'Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		self.rtspSeq += 1
		
		if requestCode == self.SETUP and self.state == self.INIT:
			self.recvRtsp_t = threading.Thread(target=self.recvRtspReply)
			self.recvRtsp_t.start()
			request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
			self.requestSent = self.SETUP
			self.playedSize = 0
			self.duration = 0
			self.packetLoss = 0
		elif requestCode == self.PLAY and self.state == self.READY:
			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent =  self.PLAY
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PAUSE
		elif requestCode == self.TEARDOWN:
			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.TEARDOWN
		elif requestCode == self.BACKKWARD:
			request = 'BACKWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.BACKKWARD
		elif requestCode == self.FORWARD:
			request = 'FORWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.FORWARD
		elif requestCode == self.DESCRIBE:
			request = 'DESCRIBE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.DESCRIBE
		else: return
		self.rtspSocket.send(request.encode())
		print('\nData sent:\n' + request)

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			if self.requestSent == self.TEARDOWN:
				break
			reply = self.rtspSocket.recv(256)
			if reply:
				if reply.decode('utf-8')[:2] == 'tt':
					self.totalTime = reply.decode('utf-8')[2:]
				else:	
					print('\n--------Reply--------\n')
					print(reply.decode('utf-8'))
					print('\n------------------------\n')
					self.parseRtspReply(reply.decode("utf-8"))
			
			

	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			if self.sessionId == 0:
				self.sessionId = session
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200:
					if self.requestSent == self.SETUP:
						self.state = self.READY
					if self.requestSent == self.PLAY:
						self.stopListeningAcked = 0
						self.state = self.PLAYING
						self.stopListeningAcked = 0	
					if self.requestSent == self.PAUSE:
						self.state = self.READY
						self.stopListeningAcked = 1					
					if self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						self.stopListeningAcked = 1

	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)		
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket.settimeout(5)	
		try:
			self.rtpSocket.bind(('', self.rtpPort))
		except:
			QMessageBox.warning(self, 'Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

