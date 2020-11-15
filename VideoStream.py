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

	def totalFrame(self, filename):	
		frame = []
		for i in self.videoData:
			#print(i)
			frame.append(i)
		self.tmpFrameNum = len(frame)
		
		return self.tmpFrameNum

	def totalTime(self):
		return float(self.tmpFrameNum / self.videoData.get_meta_data()['fps'])

	def nextFrame(self):
		if self.frameIdx >= self.tmpFrameNum:
			return None
		data = self.videoData.get_data(self.frameIdx)
		self.frameIdx += 1
		self.frameNum += 1
		buffer = io.BytesIO()
		imageio.imwrite(buffer, data, format = 'JPEG')
		return buffer.getvalue()

	def moveForward(self):		## move forward 5s - set frameIdx next to 100 frames
		if self.frameIdx > self.tmpFrameNum - 101:
			self.frameIdx = self.tmpFrameNum - 1
		else:
			self.frameIdx += 100

	def moveBackward(self):	## move backward 5s - set frameIdx back to 100 frames
		if self.frameIdx < 100:
			self.frameIdx = 0	
		else:
			self.frameIdx -= 100

	def frameNbr(self):
		"Get frame number"
		return self.frameNum
	
	def getFPS(self):
		return self.videoData.get_meta_data()['fps']
