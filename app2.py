import sys
import time
import threading

from gui import Ui_MainWindow
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from packages.pyimagesearch.centroidtrackerv2 import CentroidTracker
from controllers.StreamControllerv2 import StreamController
from controllers.DatabaseController import InventoryRepository as DatabaseController
# This file is the main file handling gui info
class MainWindow(QMainWindow, Ui_MainWindow):

	
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
		
		# Global Variables
		self.to_save_listA = None
		self.to_save_listB = None
		self.list_to_validate = None #input A or B to check which list to check
		self.flag_list_saved = False #If true, stop validation
		self.eventsA = None
		self.eventsB = None

		self.threadCam = QThread()		
		self.WorkerCamera = WorkerCamera()		
		self.WorkerCamera.moveToThread(self.threadCam)
		self.threadCam.started.connect(self.WorkerCamera.feed)
		self.WorkerCamera.SignalFeedEvents.connect(self.ImageVideoUpdate)
		self.WorkerCamera.SignalFeedEvents.connect(self.ValidateVideoFeed)   
		self.threadCam.start()
		
		self.threadValidation = QThread()
		self.ValidateFeed = ValidateFeed(parent=self)
		self.ValidateFeed.moveToThread(self.threadValidation)
		self.threadValidation.started.connect(self.ValidateFeed.validate)
		self.ValidateFeed.SignalValidation.connect(self.ValidateConfirm)
		
		

		self.db = DatabaseController()
		self.InitializeTables()

		

	# Video Feed Methods		
	def ImageVideoUpdate(self, events):
		# print(events[0][0])
		self.eventsA = events[0][0]
		self.eventsB = events[1][0] 
		frameA = QImage(self.eventsA["frame"],self.eventsA["frame"].shape[1],
			self.eventsA["frame"].shape[0], QImage.Format_RGB888).rgbSwapped()
		frameB = QImage(self.eventsB["frame"],self.eventsB["frame"].shape[1],
			self.eventsB["frame"].shape[0], QImage.Format_RGB888).rgbSwapped()
		self.ui.lblCamera1.setPixmap(QPixmap.fromImage(frameA))
		self.ui.lblCamera2.setPixmap(QPixmap.fromImage(frameB))
	def ValidateVideoFeed(self,events):
		# stores values temporarily in this instance for validation
		# event_list_A = events[0][0]
		# event_list_B = events[1][0]
		# # print("eventlists:")
		# # print(event_list_A)
		# self.to_save_listA = events[0][0]
		# self.to_save_listB = events[1][0]
		if (self.to_save_listA is None) and (bool(self.eventsA["list"])):
			self.to_save_listA = self.eventsA
		if (self.to_save_listB is None) and (bool(self.eventsB["list"])):
			self.to_save_listB = self.eventsB
		# if (not bool(self.to_save_listA["list"]) and not bool(self.to_save_listB["list"])):
		# 	print("empty_lists")
		# 	if (self.to_save_listA["objectID"] != self.to_save_listB["objectID"]):
		# 		print("AObjectID: "+str(self.to_save_listA["objectID"]))
		# 		print("BObjectID: "+str(self.to_save_listB["objectID"]))
		# 		objectIDr = min(self.to_save_listA["objectID"],self.to_save_listB["objectID"])
		# 		self.to_save_listA["centroid"].reset(objectIDr)	
		# 		self.to_save_listB["centroid"].reset(objectIDr)
		# print("listA")
		# print(self.to_save_listA)
		# print("listB")
		# print(self.to_save_listB)
		if(self.to_save_listA is not None or self.to_save_listB is not None):
			if (self.to_save_listB is None and bool(self.to_save_listA["list"])):
				self.list_to_validate = self.to_save_listB
				if not self.threadValidation.isRunning():
					print("starting thread")
					self.threadValidation.start()
			elif (self.to_save_listA is None and bool(self.to_save_listB["list"])):
				self.list_to_validate = self.to_save_listA	
				if not self.threadValidation.isRunning():
					print("threadRunning: "+str(self.threadValidation.isRunning()))
					self.threadValidation.start()
			elif (bool(self.to_save_listA["list"]) and bool(self.to_save_listB["list"])):				
				self.SaveData(self.to_save_listA, self.to_save_listB)
				objectIDA = self.to_save_listA["objectID"] if self.to_save_listA is not None else self.to_save_listB["objectID"] 
				objectIDB = self.to_save_listB["objectID"] if self.to_save_listB is not None else self.to_save_listA["objectID"]
				objectID = min(objectIDA,objectIDB)

				self.to_save_listA["centroid"].reset(objectID+1)	
				self.to_save_listB["centroid"].reset(objectID+1)  
				self.flag_list_saved = True    
				if self.threadValidation.isRunning():
					self.StopValidation()
				self.to_save_listA = None
				self.to_save_listB = None
				self.list_to_validate = None
				print("Item Recorded1")
				# print("flag_list1: "+str(self.flag_list_saved))
	def ValidateConfirm(self, result):
		if not result:
			# printtoGUI("Please try again")
			# reset all values, including CT

			objectIDA = self.to_save_listA["objectID"] if self.to_save_listA is not None else self.to_save_listB["objectID"] 
			objectIDB = self.to_save_listB["objectID"] if self.to_save_listB is not None else self.to_save_listA["objectID"]
			objectID = min(objectIDA,objectIDB)
			
			self.eventsA["centroid"].reset(objectID)	
			self.eventsB["centroid"].reset(objectID)
			self.to_save_listA = None
			self.to_save_listB = None
			self.list_to_validate = None
			self.flag_list_saved = False
			if self.threadValidation.isRunning():
				self.StopValidation()
			print("Please Try Again")
		else:
			if self.flag_list_saved:
				print("flag: "+str(self.flag_list_saved))
				print("Item has been saved")
				self.flag_list_saved = False
				# self.to_save_listA = None
				# self.to_save_listB = None
				# self.list_to_validate = None
			elif not self.flag_list_saved and (
				bool(self.to_save_listA["list"]) and bool(self.to_save_listB["list"])):
				self.SaveData(self.to_save_listA, self.to_save_listB)  
				self.flag_list_saved = False
				self.to_save_listA = None
				self.to_save_listB = None
				self.list_to_validate = None
				if self.threadValidation.isRunning():
					self.StopValidation()
				# reset all values, don't include ct
				# printtoGUI("ItemRecorded")
				print("Item Recorded2")
	def StopValidation(self):
		print("stopping thread....It will stop after finishing execution")
		self.threadValidation.quit()
		self.threadValidation.exit()
	# Database Methods
	def SaveData(self,eventA=None, eventB=None):
		# save here call db
		x=0
		
		print("Activating SaveData")
		print("printing list...")
		print(eventA["list"],eventB["list"])
		
	def UpdateData(self):
		x=0
	def InitializeTables(self):
		db = self.db
		resultsOutA = db.select_br(itemName="projector",
			date="2021-03-20 00:00:00", dateB="2021-03-20 23:59:59",
			camera=1,nametable="borrowed")
		resultsOutB = db.select_br(itemName="projector",
			date="2021-03-20 00:00:00", dateB="2021-03-20 23:59:59",
			camera=2,nametable="borrowed")
		resultsInA = db.select_br(itemName="projector",
			date="2021-03-20 00:00:00", dateB="2021-03-20 23:59:59",
			camera=1,nametable="returned")
		resultsInB = db.select_br(itemName="projector",
			date="2021-03-20 00:00:00", dateB="2021-03-20 23:59:59",
			camera=2,nametable="returned")
		for tablerow, row in enumerate(resultsOutA):
			# print(row)
			self.ui.tblWidOut1.insertRow(tablerow)
			self.ui.tblWidOut1.setItem(tablerow, 0, QTableWidgetItem(row[0]))
			self.ui.tblWidOut1.setItem(tablerow, 1, QTableWidgetItem(row[1]))
		for tablerow,row in enumerate(resultsOutB):
			# print(row)
			self.ui.tblWidOut2.insertRow(tablerow)
			self.ui.tblWidOut2.setItem(tablerow, 0, QTableWidgetItem(row[0]))
			self.ui.tblWidOut2.setItem(tablerow, 1, QTableWidgetItem(row[1]))
		for tablerow, row in enumerate(resultsInA):
			# print(row)
			self.ui.tblWidIn1.insertRow(tablerow)
			self.ui.tblWidIn1.setItem(tablerow, 0, QTableWidgetItem(row[0]))
			self.ui.tblWidIn1.setItem(tablerow, 1, QTableWidgetItem(row[1]))
		for tablerow,row in enumerate(resultsInB):
			# print(row)
			self.ui.tblWidIn2.insertRow(tablerow)
			self.ui.tblWidIn2.setItem(tablerow, 0, QTableWidgetItem(row[0]))
			self.ui.tblWidIn2.setItem(tablerow, 1, QTableWidgetItem(row[1]))
class ValidateFeed(QObject):
	SignalValidation = pyqtSignal(bool)
	def __init__(self,parent):
		super().__init__()
		self.parent = parent	
	def validate(self):
		print("thread sleeping")
		time.sleep(10)
		print("thread awake")
		print("flag_listValidateFeed: "+str(self.parent.flag_list_saved))
		if self.parent.flag_list_saved:
			print("Already Saved")
			self.SignalValidation.emit(True)
		else:
			checklist = self.parent.list_to_validate
			if checklist is None:
				print("checklist is None")
				self.SignalValidation.emit(False)
			else:
				print("checklist is not None")
				self.SignalValidation.emit(True)
	def stop(self):
		self.quit()
		self.exit()
class WorkerCamera(QObject):	
	# global variables
	SignalFeedEvents = pyqtSignal(tuple)
	def __init__(self):
		super().__init__()
		modelpath = "/home/pi/Desktop/ThesisCodes/pi_models/projector/cp109/frozen_inference_graph.bin"
		configpath = "/home/pi/Desktop/ThesisCodes/pi_models/projector/cp109/frozen_inference_graph.xml"
		
		ct1=CentroidTracker(maxDisappeared=85, maxDistance=80)
		ct2=CentroidTracker(maxDisappeared=85, maxDistance=80)

		self.Stream1=StreamController(
			model=modelpath,config=configpath,
			camera="pi",trigger_conf="W2",frameskip=32, 
			confidence=0.90, ct=ct1)
		
		self.Stream2=StreamController(
			model=modelpath,config=configpath,
			camera="webcam",trigger_conf="W2",frameskip=32,
			confidence=0.90, ct=ct2)
		
		self.dataA = None
		self.dataB = None

	def feed(self):
		Stream1 = self.Stream1
		Stream2 = self.Stream2
		# self.ThreadActive = True
		collection1 = Stream1.stream()		
		collection2 = Stream2.stream()
		
		# while self.ThreadActive:
		for collections in zip(collection1, collection2):
			for collection in zip(collections, ("collect1","collect2")):
				if self.dataA is None and collection[1]=="collect1":
					self.dataA = collection
				elif self.dataB is None and collection[1]=="collect2":
					self.dataB = collection
				if (self.dataA is not None) and (self.dataB is not None):
					# self.SignalFeedEvents.emit(collection)
					self.SignalFeedEvents.emit((self.dataA,self.dataB))
					if (bool(self.dataA[0]["list"])):
						print("Workerfeed")
						print(self.dataA[0]["list"])
					if (bool(self.dataB[0]["list"])):
						print(self.dataB[0]["list"])
					self.dataA = None
					self.dataB = None
						

					# print(collection)
					# print("pika")
					# frame = QImage(collection[0]["frame"], collection[0]["frame"].shape[1], collection[0]["frame"].shape[0],
					# 	QImage.Format_RGB888).rgbSwapped()
					# if collection[1] == "collect1":
					# 	self.SignalFeedEvents.emit(frame,"frame1") #Pass a data structure instead
					# else:
					# 	self.SignalFeedEvents.emit(frame,"frame2")	

	def stop(self):
		self.ThreadActive = False
		self.quit()
if __name__ == "__main__":
	App = QApplication(sys.argv)
	Window = MainWindow()
	Window.show()
	sys.exit(App.exec())