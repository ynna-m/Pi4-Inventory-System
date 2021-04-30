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
		self.threadcam.started.connect(self.WorkerCamera.feed)
		self.WorkerCamera.SignalFeedEvents.connect(self.ImageVideoUpdate)
		self.WorkerCamera.SignalFeedEvents.connect(self.ValidateVideoFeed)   
		self.threadcam.start()
		
		self.threadvalidation = QThread()
		# self.threadvalidation.started.connect(self.Val)

		self.db = DatabaseController()
		self.InitializeTables()
	# Video Feed Methods		
	def ImageVideoUpdate(self, events):
		# print(events[0][0])
		frameA = QImage(events[0][0]["frame"],events[0][0]["frame"].shape[1],
			events[0][0]["frame"].shape[0], QImage.Format_RGB888).rgbSwapped()
		frameB = QImage(events[1][0]["frame"],events[1][0]["frame"].shape[1],
			events[1][0]["frame"].shape[0], QImage.Format_RGB888).rgbSwapped()
		self.ui.lblCamera1.setPixmap(QPixmap.fromImage(frameA))
		self.ui.lblCamera2.setPixmap(QPixmap.fromImage(frameB))
		# old code
		# frame = QImage(frame, frame.shape[1], frame.shape[0],
		# 				QImage.Format_RGB888).rgbSwapped()
		# if lbl == "collect2":
		# 	self.ui.lblCamera2.setPixmap(QPixmap.fromImage(frame))
		# else:
		# 	self.ui.lblCamera1.setPixmap(QPixmap.fromImage(frame))	
	def ValidateVideoFeed(self, events):
		# Decide here whether to save data or alert user
		# if mismatch, popup alert window and sleep workercamera.
		# to_save_listA = events[0][0]["list"]
		# ct1 = events[0][0]["centroid"]
		# to_save_listB = events[1][0]["list"]
		# ct2 = events[1][0]["centroid"]
		# if (to_save_listA) and (to_save_listB is None):
		# 	print("first")
		# elif(to_save_listA is None) and (to_save_listB):
		# 	print("second")
		# elif(to_save_listA) and (to_save_listB):
		# 	print("third")
		# for objectID
		x=0
		# if x == 1: #placeholder
		# 	self.WorkerCamera.sleep()
		# # else
		# elif x == 2:
		# 	self.SaveData(events)
	# Database Methods
	def SaveData(self,events):
		# save here call db
		x=0
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
# class ValidateFeed(QObject):
# 	def __init__():
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
					if (self.dataA[0]["list"] is not None):
						print(self.dataA[0]["list"])
					if (self.dataB[0]["list"] is not None):
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