from socket import timeout
from threading import Thread, current_thread
from PySide2.QtWidgets import QWidget,QPushButton, QMessageBox, QLabel, QApplication, QSlider, QVBoxLayout, QHBoxLayout
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtCore import Qt,QSize
from PIL import Image
import socket, threading, sys, traceback, os
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

	
class Client(QWidget):
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
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
		self.frameNbr = 0

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

		infoBtn = QPushButton("", self)
		infoBtn.setFixedWidth(150)
		infoBtn.setIcon(QIcon('info.icon'))
		infoBtn.setIconSize(QSize(30,30))
		infoBtn.clicked.connect(self.describeMovie)
		#HBoxLayout
		hBox = QHBoxLayout()
		hBox.setContentsMargins(0,0,0,0)
		#hBox.addWidget(setupBtn)
		hBox.addWidget(infoBtn)
		hBox.addWidget(bwBtn)
		hBox.addWidget(playBtn)
		hBox.addWidget(pauseBtn)
		hBox.addWidget(fwBtn)
		hBox.addWidget(stopBtn)
		#VBoxLayout
		vBox = QVBoxLayout()
		vBox.addWidget(self.label)
		vBox.addWidget(slider)
		vBox.addLayout(hBox)	
		vBox.addStretch()
		self.setLayout(vBox)

	def bwMovie(self):
		# if self.state == self.PLAYING or self.state == self.READY:
		# 	self.sendRtspRequest(self.BACKKWARD)
		pass
	def fwMovie(self):
		# if self.state == self.PLAYING or self.state == self.READY:
		# 	self.sendRtspRequest(self.BACKKWARD)
		pass

	def describeMovie(self):
		pass

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
		self.sendRtspRequest(self.TEARDOWN)
		self.recvRtsp_t.join()
		self.play_t.join()
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
			self.stopListeningAcked = 1
			
	
	def playMovie(self):
		"""Play button handler."""
		#TODO
		#if self.firstPlay == 0:
		if self.state == self.READY:
			self.sendRtspRequest(self.PLAY)
			self.play_t = threading.Thread(target = self.listenRtp)
			self.play_t.start()
			
			
				
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		while True:
			print("ack = ", self.stopListeningAcked)
			try:
				print(threading.active_count())
				data = self.rtpSocket.recv(20480)   ## Why 20480?
				if data:
					rtpPacket = RtpPacket() 		## In reality, is the RtpPacket.py the same place as Client.py?
					rtpPacket.decode(data)
					current_frame = rtpPacket.seqNum()
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
		elif requestCode == self.PLAY and self.state == self.READY:
			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent =  self.PLAY
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PAUSE
		elif requestCode == self.TEARDOWN:
			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.TEARDOWN
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
						self.openRtpPort()
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
		self.rtpSocket.settimeout(0.5)	
		try:
			self.rtpSocket.bind(('', self.rtpPort))
		except:
			QMessageBox.warning(self, 'Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

