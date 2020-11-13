import sys
from time import time
from VideoStream import VideoStream

fileName = 'movie.Mjpeg'
obj = VideoStream(fileName)

obj.totalFrame()
obj.nextFrame()
print(int(obj.file.read(5)))
# obj.nextFrame()
# obj.nextFrame()
# obj.nextFrame()
# obj.nextFrame()
# obj.nextFrame()

print(round(float(time()),2))

# print(obj.frameIdx)
# print(obj.frameNum)
# obj.moveBackward()
# print(obj.frameIdx)
# print(int(obj.file.read(5)))
# obj.moveBackward()
# print(int(obj.file.read(5)))
# obj.moveForeward()
# print(obj.frameIdx)
# print(int(obj.frameTrack[2], 0) - int(obj.frameTrack[1], 0))