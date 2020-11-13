class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
			self.tmpFile = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		self.tmpFrameNum = 0
		self.frameIdx = 0
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		self.frameIdx += 1
		if data: 
			framelength = int(data)			
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data

	def totalFrame(self):
		self.frameTrack = []
		count = '0'
		while True:
			self.frameTrack.append(count)		#store position of the firstbyte of the frame
			tmpData = self.tmpFile.read(5)
			if tmpData:
				tmpFramelength = int(tmpData)
				count = str(hex(int(count, 16) + 5 + tmpFramelength))			#convert position of the first byte to hex then to string
				tmpData = self.tmpFile.read(tmpFramelength)
				self.tmpFrameNum += 1
			else:
				return self.tmpFrameNum			#total frame number
	
	def totalTime(self):
		print(self.frameTrack[500])
		return float(self.tmpFrameNum / 20)
		
	def moveBackward(self):	#move backward 5s
		index = '0'
		if self.frameIdx > 100:
			index = self.frameTrack[self.frameIdx - 100]
			self.frameIdx -= 100
		else:
			self.frameIdx = 0
		self.file.seek(int(index, 0), 0)

	def moveForward(self): #move foreward 5s
		index = str(self.tmpFrameNum - 1)
		if self.frameIdx < self.tmpFrameNum - 100:
			index = self.frameTrack[self.frameIdx + 100]
			self.frameIdx += 100
		else:
			self.frameIdx = int(index)
			index = self.frameTrack[int(index)]
		self.file.seek(int(index, 16), 0)

	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum