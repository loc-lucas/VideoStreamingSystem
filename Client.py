from socket import timeout
from threading import Thread, current_thread
from PySide2.QtWidgets import QWidget,QPushButton, QMessageBox, QLabel
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtCore import Qt
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
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.setWindowTitle("Promise")
		self.label = QLabel(self)
		self.label.resize(800,600)
		self.setGeometry(1000,600,800,600)
		self.setIcon()
		self.setButton()

	def setIcon(self):
		appIcon = QIcon("image.icon")
		self.setWindowIcon(appIcon)
	def setButton(self):
		btn1 = QPushButton("Setup", self)
		btn1.move(50,500)	
		btn1.clicked.connect(self.setupMovie)
		btn2 = QPushButton("Play", self)
		btn2.move(250,500)
		btn2.clicked.connect(self.playMovie)
		btn3 = QPushButton("Pause", self)
		btn3.move(450,500)
		btn3.clicked.connect(self.pauseMovie)
		btn4 = QPushButton("Tear down", self)
		btn4.move(650,500)
		btn4.clicked.connect(self.exitClient)
	def closeEvent(self ,event):
		self.client.handler()
	def setupMovie(self):
		"""Setup button handler."""
		#TODO
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
		#TODO
		self.sendRtspRequest(self.TEARDOWN)
		self.master.destroy() ### close the GUI window

	def pauseMovie(self):
		"""Pause button handler."""
		#TODO
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		#TODO
		if self.state == self.READY:
			new_t = threading.Thread(target = self.listenRtp)
			new_t.start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		while True:
			try:
				data = self.rtpSocket.recv(20480)   ## Why 20480?
				if data:
					rtpPacket = RtpPacket() 		## In reality, is the RtpPacket.py the same place as Client.py?
					rtpPacket.decode(data)
					current_frame = rtpPacket.seqNum()
					if current_frame > self.frameNbr:
						self.frameNbr = current_frame
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# if self.playEvent.isSet():
				# 	break
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()  ## can we close socket without shutting down it
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
		self.label.setPixmap(self.pixmap)

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		#TODO
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			QMessageBox.Warning(self,'Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		self.rtspSeq += 1
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
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
			reply = self.rtspSocket.recv(256)
			if reply:
				print('\n--------Reply--------\n')
				print(reply.decode('utf-8'))
				print('\n------------------------\n')
				self.parseRtspReply(reply.decode("utf-8"))
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
			

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
						self.state = self.PLAYING
					if self.requestSent == self.PAUSE:
						self.state = self.READY
						####
					if self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						self.teardownAcked = 1

	
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
			QMessageBox.Warning(self, 'Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		self.pauseMovie()
		userInfo = QMessageBox.question(self, 'Confirmation', 'Do you want to close?', QMessageBox.Yes, QMessageBox.No)
		if userInfo == QMessageBox.Yes:
			self.exitClient()
		elif userInfo == QMessageBox.No:
			self.playMovie()