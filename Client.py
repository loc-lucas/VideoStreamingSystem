from socket import timeout
from threading import Thread, current_thread
from PySide2.QtWidgets import QWidget,QPushButton, QMessageBox, QLabel
from PySide2.QtWidgets import QApplication, QSlider, QVBoxLayout, QHBoxLayout, QSizePolicy, QComboBox
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtCore import Qt,QSize
from time import time
from PIL import Image
import socket, threading, sys, traceback, os
import imageio
from RtpPacket import RtpPacket
CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"
import json
import math
class Client(QWidget):
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCH = 3
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
		self.checkPause = 0
		self.connectToServer()
		self.openRtpPort()
		
		self.listVideoName = []
		self.listFileName = []
		self.listDuration = []
		
		self.frameNbr = 0
		self.totalTime = 0
		self.replySent = 0
		self.videoDuration = 0
		self.comboFlag = 1
		self.realFrameNbr = 0
		self.moveFlag = 0
		self.backFlag = 0
		self.init_ui()

	def init_ui(self):
		self.setWindowTitle("Promise")
		self.setGeometry(800,450,800,450)
		#Video screen
		self.videoScreen = QLabel(self)
		self.videoScreen.setMinimumSize(800,450)
		self.videoScreen.setStyleSheet("QWidget {background-color: rgba(0,0,0,1);}")
		self.videoScreen.setAlignment(Qt.AlignCenter)
		self.videoScreen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		#Apps icon
		appIcon = QIcon("image.icon")
		self.setWindowIcon(appIcon)
		#Create buttons
		playBtn = QPushButton("", self)
		playBtn.setIconSize(QSize(30,30))
		playBtn.setIcon(QIcon('play.icon'))
		playBtn.clicked.connect(self.playMovie)
		playBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		playBtn.setBaseSize(100,50)
		
		pauseBtn = QPushButton("", self)
		pauseBtn.setIconSize(QSize(30,30))
		pauseBtn.setIcon(QIcon('pause.icon'))
		pauseBtn.clicked.connect(self.pauseMovie)
		pauseBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		stopBtn = QPushButton("", self)
		stopBtn.setIcon(QIcon('stop.icon'))
		stopBtn.setIconSize(QSize(30,30))
		stopBtn.clicked.connect(self.stopMovie)
		stopBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		bwBtn = QPushButton("", self)
		bwBtn.setIcon(QIcon('backward.icon'))
		bwBtn.setIconSize(QSize(30,30))
		bwBtn.clicked.connect(self.bwMovie)
		bwBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		fwBtn = QPushButton("", self)
		fwBtn.setIcon(QIcon('forward.icon'))
		fwBtn.setIconSize(QSize(30,30))
		fwBtn.clicked.connect(self.fwMovie)
		fwBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		infoBtn = QPushButton("", self)
		infoBtn.setIcon(QIcon('info.icon'))
		infoBtn.setIconSize(QSize(30,30))
		infoBtn.clicked.connect(self.describeMovie)
		infoBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		switchMovieBtn = QPushButton("Switch Video", self)
		switchMovieBtn.setFixedSize(180,50)
		switchMovieBtn.setIconSize(QSize(30,30))
		switchMovieBtn.clicked.connect(self.chooseVid)
		switchMovieBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		self.comboBox = QComboBox(self)
		self.comboButton = QPushButton("Choose Video", self)
		self.comboButton.clicked.connect(self.switchVid)
		#Statistic box vertical layout
		statisticBox = QVBoxLayout()
		self.videoRateLabel = QLabel(self)
		self.videoRateLabel.setMinimumSize(180,50)
		self.videoRateLabel.setAlignment(Qt.AlignTop)
		statisticBox.addWidget(self.videoRateLabel)
		statisticBox.addWidget(switchMovieBtn)
		statisticBox.addWidget(self.comboButton)
		statisticBox.addWidget(self.comboBox)

		#HBoxLayout
		hBox = QHBoxLayout()
		hBox.setContentsMargins(0,0,0,0)
		hBox.addWidget(infoBtn)
		hBox.addWidget(bwBtn)
		hBox.addWidget(playBtn)
		hBox.addWidget(fwBtn)
		hBox.addWidget(pauseBtn)
		hBox.addWidget(stopBtn)
		#VideoBox layout
		videoBox = QHBoxLayout()
		videoBox.setContentsMargins(0,0,0,0)
		videoBox.addWidget(self.videoScreen)
		videoBox.addLayout(statisticBox)

		# #VBoxLayout
		vBox = QVBoxLayout()
		vBox.addLayout(videoBox)
		vBox.addLayout(hBox)
		# vBox.addWidget(chooseVideoBtn)	
		vBox.addStretch()
		#vBox.addLayout(StatisticBox)
		self.setLayout(vBox)	

	def bwMovie(self):
		if self.state == self.PLAYING or self.state == self.READY:
			self.backFlag = 1
			self.sendRtspRequest(self.BACKKWARD)
	def fwMovie(self):
		if self.state == self.PLAYING or self.state == self.READY:
			self.moveFlag = 1
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
		
	def showTotalTime(self):
		print(self.totalTime)

	def switchVid(self):
		try:
			self.fileName = self.listFileName[self.comboBox.currentIndex()]
			self.comboBox.clear()
			self.stopMovie()
		except:
			pass
		

	def chooseVid(self):
		self.comboBox.clear()
		# if self.requestSent == self.PLAY:
		# 	self.play_t.join()
		self.sendRtspRequest(self.GETLIST)  #self.state = SWITCH
		self.comboBox.addItems(self.listVideoName)
		self.listVideoName = []
		self.listFileName = []
		self.listDuration = []
		self.state = self.SWITCH
		self.comboBox.showPopup()


	def stopMovie(self):
		if (self.requestSent == self.PAUSE and self.state == self.READY) or self.requestSent == self.PLAY or self.state == self.SWITCH:
			self.sendRtspRequest(self.TEARDOWN)
			# self.play_t.join()
			self.recvRtsp_t.join()
			self.rtspSeq = 0
			self.sessionId = 0
			self.requestSent = -1
			self.stopListeningAcked = 0
			self.frameNbr = 0	
			self.videoRateLabel.clear()
			self.videoScreen.clear()
			self.realFrameNbr = 0
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
		self.master.quit()
	def pauseMovie(self):
		"""Pause button handler."""
		#TODO
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
			self.duration += round(float(time()),2) - self.startTime ## calculate total duration
			self.startTime = 0										 ## set start time of the duration to 0
			self.checkPause = 1										 ## check if pause is used at least once
			#self.stopListeningAcked = 1
			#self.play_t.join()	
			
	
	def playMovie(self):
		"""Play button handler."""
		#TODO
		if self.state == self.READY or self.state == self.SWITCH:
			self.startTime = round(float(time()),2)	#set start time of the duration when press PLAY
			self.sendRtspRequest(self.PLAY)
			self.play_t = threading.Thread(target = self.listenRtp)
			self.play_t.start()
		print(self.videoDuration)
	
	def videoRate(self):
		"""calculate video rate (bit/s)"""
		#videoSize = 1 ##  take from the description
		if self.checkPause == 0 and self.videoDuration != 0:
			self.duration = self.videoDuration
			bitRate = round(float(self.playedSize) / self.duration, 2)
		elif self.checkPause == 0 and self.videoDuration == 0:
			bitRate = 0
		else:
			bitRate = round(float(self.playedSize) / self.duration, 2)
		#print(self.rtpLossRate(25))
		self.videoRateLabel.setText("Video Rate: " + str(bitRate) + " byte/s\nLoss Rate: "
		 + str(self.rtpLossRate(self.totalTime * float(self.fps))) + " %"
		 + "\nCurrent Time: " + str(self.currentTime()) + "s"
		 + "\nRemaining Time: "  + str(self.remainTime()) + "s")
	def currentTime(self):
		tmp = self.realFrameNbr / int(self.fps)
		if tmp < 0:
			tmp = 0
		elif tmp > self.totalTime: tmp = self.totalTime
		return math.ceil(tmp) if self.totalTime - tmp > 0 else math.floor(tmp)

	def remainTime(self):
		tmp = tmp = self.totalTime - float(self.realFrameNbr / int(self.fps))
		if tmp < 0:
			tmp = 0
		elif tmp > self.totalTime: tmp = self.totalTime

		return math.floor(tmp) if tmp > 0 else math.ceil(tmp)

	def rtpLossRate(self, totalPacket):
		"""calculate RTP packet loss rate"""
		lossRate = self.packetLoss / totalPacket
		# print(self.packetLoss)
		return round(lossRate,2)*100

	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		while True:
			#print("ack = ", self.stopListeningAcked)
			try:
				#print(threading.active_count())
				data = self.rtpSocket.recv(20480)   ## Why 20480?
				if data:
					rtpPacket = RtpPacket() 		## In reality, is the RtpPacket.py the same place as Client.py?
					rtpPacket.decode(data)
					current_frame = rtpPacket.seqNum()
					if current_frame - self.frameNbr > 1 :
						self.packetLoss += current_frame - self.frameNbr - 1
					self.lastSeq = current_frame
					self.videoDuration = round(float(time()),2) - self.startTime - 0.05*2
					self.videoRate()
					if current_frame > self.frameNbr:
						if self.moveFlag == 0 and self.backFlag == 0:
							self.realFrameNbr += 1
						elif self.moveFlag == 1:
							self.realFrameNbr += 5 * int(self.fps)
							self.moveFlag = 0
						elif self.backFlag == 1:
							self.realFrameNbr -= 5 * int(self.fps)
							self.backFlag = 0
						self.frameNbr = current_frame
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
				else:
					self.lastSeq = self.totalTime * 20
					self.videoRate()
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
		self.playedSize += os.path.getsize(file_name)	## total played video size
		return file_name

	def updateMovie(self, imageFile):
		self.pixmap = QPixmap(imageFile)
		w = self.width()
		h = self.height()

		self.videoScreen.setPixmap(self.pixmap.scaled(w,h,Qt.KeepAspectRatio))

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
		elif (requestCode == self.PLAY and self.state == self.READY) or (requestCode == self.PLAY and self.state == self.SWITCH):
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
		elif requestCode == self.GETLIST:
		 	request = 'GETLIST ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
		 	self.requestSent = self.GETLIST
		else: return
		self.rtspSocket.send(request.encode())
		print('\nData sent:\n' + request)

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			if self.requestSent == self.TEARDOWN:
				break
			reply = self.rtspSocket.recv(256).decode('utf-8')
			if reply:
				if reply.split(' ')[0] == 'tt':
					self.totalTime = float(reply.split(' ')[1])
					self.fps = float(reply.split(' ')[2])
				elif reply[:2] == 'cc':
					self.parseRtspReply(reply[2:])
				else:
					print('\n--------Reply--------\n')
					print(reply)
					print('\n------------------------\n')
					self.parseRtspReply(reply)
			
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		try:
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
							self.state = self.PLAYING
							self.stopListeningAcked = 0	
						if self.requestSent == self.PAUSE:
							self.state = self.READY
							self.stopListeningAcked = 1
						if self.requestSent == self.TEARDOWN:
							self.state = self.INIT
							self.stopListeningAcked = 1
						if self.requestSent == self.GETLIST:
							self.state = self.SWITCH
							self.stopListeningAcked = 1
							self.listVideoName = []
							self.listFileName = []
							self.listDuration = []
							for i in lines[3:]:
								self.listVideoName += [i.split(',')[0]]		
								self.listFileName += [i.split(',')[1]]
								self.listDuration += [i.split(',')[2]]

		except:
			if self.requestSent == self.DESCRIBE:
				sdp = open("sdp.txt","w")
				# sdp.write(data)
				sdp.write(data)
				sdp.close()
				sdp = open("sdp.txt","r")
				for line in sdp.readlines():
					line.replace("\n","")
					print(line)
				sdp.close()


	
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

