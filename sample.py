import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
# from PyQt5 import QtWidgets as qtw
# from PyQt5 import QtCore as qtc
# from PyQt5 import QtGui as qtg
import cv2
import imutils
from imutils.video import VideoStream
import time

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.VBL = QVBoxLayout()

        self.FeedLabel = QLabel()
        self.VBL.addWidget(self.FeedLabel)

        self.CancelBTN = QPushButton("Cancel")
        self.CancelBTN.clicked.connect(self.CancelFeed)
        self.VBL.addWidget(self.CancelBTN)

        self.Worker1 = Worker1()

        self.Worker1.start()
        self.Worker1.ImageUpdate.connect(self.ImageUpdateSlot)
        self.setLayout(self.VBL)

    def ImageUpdateSlot(self, Image):
        self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

    def CancelFeed(self):
        self.Worker1.stop()

class Worker1(QThread):
    ImageUpdate = pyqtSignal(QImage)
    def run(self):
        self.ThreadActive = True
        # Capture = cv2.VideoCapture(0)
        vs = VideoStream(usePiCamera=True).start()
        time.sleep(2.0)
        while self.ThreadActive:            
            frame = vs.read()
            frame = imutils.resize(frame, width=300)
            frame = QImage(frame, frame.shape[1], frame.shape[0],
                QImage.Format_RGB888).rgbSwapped()
            self.ImageUpdate.emit(frame)            
    def stop(self):
        self.ThreadActive = False
        self.quit()

if __name__ == "__main__":
    App = QApplication(sys.argv)
    Root = MainWindow()
    Root.show()
    sys.exit(App.exec())