import sys
import time
import threading

from gui import Ui_MainWindow
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from packages.pyimagesearch.centroidtracker import CentroidTracker
from controllers.StreamControllerv2 import StreamController
from controllers.DatabaseController import InventoryRepository as DatabaseController
# This file is the main file handling gui info
class MainWindow(QMainWindow, Ui_MainWindow):
	to_save_listA = None
	to_save_listB = None
	validateflagA = False
	validateflagB = False
	timerthreadflag = False
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# GUI initializations
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.ui.dateTimeEditFrom.setDate(QDate.currentDate())
		self.ui.dateTimeEditTo.setDate(QDate.currentDate())
		self.ui.dateTimeEditFrom.setTime(QTime(0,0,0))
		self.ui.dateTimeEditTo.setTime(QTime(23,59,59))
		
		loadgif = QMovie("img/loading.gif")
		self.ui.lblCamera1.setMovie(loadgif)
		self.ui.lblCamera2.setMovie(loadgif)
		loadgif.start()
		
		self.threadcam = QThread()		
		self.WorkerCamera = WorkerCamera()		
		self.WorkerCamera.moveToThread(self.threadcam)
		self.threadcam.started.connect(self.WorkerCamera.run)
		self.WorkerCamera.SignalFeedEvents.connect(self.VideoFeedParser)
		# self.WorkerCamera.SignalFeedEvents.connect(self.ValidateVideoFeed)   
		self.threadcam.start()
		
		self.threadvalidation = QThread()
		self.ValidateFeed = None
		self.threadvalidation.started.connect(self.ValidateVideoFeed())
		# self.threadvalidation.started.connect(self.Val)

		connect(self.VideoFeedParser)
		connect()
	# Video Feed Methods
	def VideoFeedParser(self, events):
		self.ImageVideoUpdate(events)
		self.ValidateVideoFeed(events):
	def ImageVideoUpdate(self, events):
		frameA = QImage(events[0][0]["frame"],events[0][0]["frame"].shape[1],
			events[0][0]["frame"].shape[0], QImage.Format_RGB888).rgbSwapped()
		frameB = QImage(events[1][0]["frame"],events[1][0]["frame"].shape[1],
			events[1][0]["frame"].shape[0], QImage.Format_RGB888).rgbSwapped()
		self.ui.lblCamera1.setPixmap(QPixmap.fromImage(frameA))
		self.ui.lblCamera2.setPixmap(QPixmap.fromImage(frameB))
	def ValidateVideoFeed(self, events):
		to_save_listA = events[0][0]["list"]
		ct1 = events[0][0]["centroid"]
		to_save_listB = events[1][0]["list"]
		ct2 = events[1][0]["centroid"]
		if (to_save_listA is not None) and (to_save_listB is None):
			if(self.ValidateFeed is None):
				self.ValidateFeed = ValidateFeed(to_save_listB)
				self.ValidateFeed.moveToThread(self.threadvalidation)
				self.ValidateFeed.SignalValidation.connect()
			else:
				self.ValidateFeed = ValidateFeed(to_save_listB)
		elif (to_save_listA is not None) and (to_save_listB is None):
			if(self.ValidateFeed is None):
				self.ValidateFeed = ValidateFeed(to_save_listA)
				self.ValidateFeed.moveToThread(self.threadvalidation)
				self.ValidateFeed.SignalValidation.connect()
	def store_list_save(self, events):
		# temporarily stores for validation
	def list_save(self, events):
		# saves to database
		x=0
		# if validatefeed confirms there is to_save_listA:
			#to_save_listA = events [save]
		# elif b
			# to_save_listB = events [save]
class ValidateFeed(QObject):
	SignalValidation = pyqtSignal(tuple)
	def __init__(self, to_save_list=None):
		


class WorkerCamera(QObject):
	# global variables

	Stream1=StreamController(
		model=modelpath,config=configpath,
		camera="pi",trigger_conf="W2",frameskip=32, 
		confidence=0.90, ct=ct1)
	Stream2=StreamController(
		model=modelpath,config=configpath,
		camera="webcam",trigger_conf="W2",frameskip=32,
		confidence=0.90, ct=ct2)
	

	SignalFeedEvents = pyqtSignal(tuple)
	def run(self):
		Stream1 = self.Stream1
		Stream2 = self.Stream2
		# self.ThreadActive = True
		collection1 = Stream1.stream()		
		collection2 = Stream2.stream()
		
		# while self.ThreadActive:
		for collections in zip(collection1, collection2):
			for collection in zip(collections, ("collect1","collect2")):				
					self.SignalFeedEvents.emit((self.dataA,self.dataB))
				


	def stop(self):
		self.ThreadActive = False
		self.quit()
if __name__ == "__main__":
	App = QApplication(sys.argv)
	Window = MainWindow()
	Window.show()
	sys.exit(App.exec())