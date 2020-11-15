import imageio
import io
class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
			self.tmpFile = open(filename, 'rb')
			self.videoData = imageio.get_reader(filename, 'ffmpeg')		## read data of video into matrix
		except:
			raise IOError
		self.frameNum = 0
		self.tmpFrameNum = 0
		self.frameIdx = 0

	def totalFrame2(self, filename):	
		frame = []
		for i in self.videoData:
			#print(i)
			frame.append(i)
		self.tmpFrameNum = len(frame)
		
		return self.tmpFrameNum

	def totalTime2(self):
		return float(self.tmpFrameNum / 20)

	def nextFrame2(self):
		if self.frameIdx >= self.tmpFrameNum:
			return None
		data = self.videoData.get_data(self.frameIdx)
		self.frameIdx += 1
		self.frameNum += 1
		buffer = io.BytesIO()
		imageio.imwrite(buffer, data, format = 'JPEG')
		return buffer.getvalue()

	def moveForward2(self):		## move forward 5s - set frameIdx next to 100 frames
		if self.frameIdx > self.tmpFrameNum - 101:
			self.frameIdx = self.tmpFrameNum - 1
		else:
			self.frameIdx += 100

	def moveBackward2(self):	## move backward 5s - set frameIdx back to 100 frames
		if self.frameIdx < 100:
			self.frameIdx = 0	
		else:
			self.frameIdx -= 100

#-------------------------------------------------Mjpeg-------------------------------------------------

	def nextFrame(self):
		"Get next frame"
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
		"Get frame number"
		return self.frameNum
	
	
