import sys
from Client import Client
from PySide2.QtWidgets import QApplication
	
if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	
	myApp = QApplication(sys.argv)

	# Create a new client
	fileName = 'movie1.Mjpeg'
	app = Client(myApp, serverAddr, serverPort, rtpPort, fileName)
	app.show()
	myApp.exec_()
	