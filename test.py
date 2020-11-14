import imageio
import io
import numpy as np
im = imageio.get_reader('movie2.mjpeg', 'ffmpeg')
data = im.get_data(0)
buffer = io.BytesIO()
imageio.imwrite(buffer, data, format='JPEG')
file_name = 'chelsea.jpg'
# print(buffer.getvalue())
temp_file = open(file_name, 'wb') ## open in binary format and write
temp_file.write(buffer.getvalue())
temp_file.close()

# frame = []
# for i in im:
#     frame.append(i)
# print(len(im))
#imageio.imwrite('chelsea.jpg', im.get_data(200))

#pic = list(im.get_data(0).flatten())

#print(l.shape)
# l = bytearray(np.array(l).tobytes())
# l = np.array(l).reshape(368,640,3)
# print(l)

# l = l.reshape(368,640,3)
# a.tobytes()
# print(l)

#print(im.get_length())