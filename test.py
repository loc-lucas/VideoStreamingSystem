import imageio
import io

class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = imageio.get_reader(filename, 'ffmpeg')
        except:
            raise IOError
        self.frameNum = 0
        self.currFrameIdx = 0
        
    def nextFrame(self):
        """Get next frame."""
        data = self.file.get_data(self.currFrameIdx)
        self.currFrameIdx += 1
        self.frameNum += 1
        buffer = io.BytesIO()
        imageio.imwrite(buffer, data, format='JPEG')
        return buffer.getvalue()
        
    def frameNbr(self):
        """Get frame number."""
        return self.frameNum

var = VideoStream('movie2.mjpeg')
data = var.nextFrame()
file_name = 'arsenal.jpg'
temp_file = open(file_name, 'wb') ## open in binary format and write
temp_file.write(data)
temp_file.close()
#imageio.imwrite(file_name, np.array(data[3:]).reshape(data[0],data[1],3))
	
	