from packages.pyimagesearch.trackableobject import TrackableObject
from packages.thesisdatabase.mysql_inventory import InventoryRepository
from controllers.NonMaxSuppression import NonMaxSuppression
from imutils.video import VideoStream
from imutils.video import FPS
from datetime import datetime as dt
import numpy as np

import imutils
import time
import dlib
import cv2

class StreamController:
	# serves as 1 instance of camera
	def __init__(self, model=None, config=None, confidence=0.80, 
		frameskip=25, camera="pi", trigger_conf=None, ct=None):
		self.model = model
		self.config = config
		self.confidence = confidence
		self.frameskip = frameskip
		self.camera = camera
		self.trigger_conf = trigger_conf
		self.ct = ct # centroid tracker
		print(camera)
	def stream(self):
		model = self.model
		config = self.config
		confidence = self.confidence
		frameskip = self.frameskip
		camera = self.camera

		nms_c = NonMaxSuppression()
		
		print("[INFO] loading model...")
		net = cv2.dnn.readNet(model=model, config=config)
		net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

		CLASSES = ["none","projector"]
		db = InventoryRepository()

		vs = None
		
		print("[INFO] starting video stream...")
		if camera == "pi":
			vs = VideoStream(usePiCamera=True).start()
			time.sleep(2.0)
		elif camera == "webcam":            
			camsrc = 0
			while True:
				vs = VideoStream(src=camsrc).start()
				time.sleep(2.0)
				frame = vs.read()
				if frame is None:
					vs.stop()
					camsrc+=1
				else:
					break
		# initialize the frame dimensions (we'll set them as soon as we read
		# the first frame from the video)
		W = None
		H = None

		# instantiate our centroid tracker, then initialize a list to store
		# each of our dlib correlation trackers, followed by a dictionary to
		# map each unique object ID to a TrackableObject
		ct = self.ct
		trackers = []
		trackableObjects = {}
		totalFrames = 0
		totalDown = 0
		totalUp = 0
		object_ID = 0 #for_statusviewing
		object_ID_s = 0 #for_comparisonto object_ID
		passed = 0 # event trigger
		datetime = ""
		item_stat = ""
		to_save_list = {}
		flag_idchanged = None
		flag_justcreated = False
		flag_reset = None
		# start the frames per second throughput estimator
		fps = FPS().start()

		while True:
			# output_frames = []
			frame = vs.read()

			# resize the frame to have a maximum width of 500 pixels (the
			# less data we have, the faster we can process it), then convert
			# the frame from BGR to RGB for dlib
			frame = imutils.resize(frame, width=300)
			rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			# if the frame dimensions are empty, set them
			if W is None or H is None:
				(H, W) = frame.shape[:2]
			# initialize the current status along with our list of bounding
			# box rectangles returned by either (1) our object detector or
			# (2) the correlation trackers
			status = "Waiting"
			rects = []
			# check to see if we should run a more computationally expensive
			# object detection method to aid our tracker
			if totalFrames % frameskip == 0:
				# set the status and initialize our new set of object trackers
				status = "Detecting"
				trackers = []
				# convert the frame to a blob and pass the blob through the
				# network and obtain the detections
				blob = cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False)
				net.setInput(blob)
				detections = net.forward()
				rectangles = []
				# loop over the detections
				for i in np.arange(0, detections.shape[2]):
					# extract the confidence (i.e., probability) associated
					# with the prediction           
					d_confidence = detections[0, 0, i, 2]
					# filter out weak detections by requiring a minimum
					# confidence
					if d_confidence > confidence:
						# extract the index of the class label from the
						# detections list
						# [0, 0, i, 1] = index of class label
						# [0, 0, i, 2] = confidence in decimal
						# [0, 0, i, 3:7(or 3-6)] = bounding box coordinates

						idx = int(detections[0, 0, i, 1])
						
						# if the class label is not a projector, ignore it
						if CLASSES[idx] != "projector":
							continue

						# compute the (x, y)-coordinates of the bounding box
						# for the object
						box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
						(startX, startY, endX, endY) = box.astype("int")
						
						rectangles.append((startX,startY,endX,endY))                       
				rectboxes = np.array(rectangles,dtype="float64")
				# Remove Extra Detections
				nms = nms_c.non_max_suppression_fast(rectboxes,0.03)
				for i in nms:               
					# construct a dlib rectangle object from the bounding
					# box coordinates and then start the dlib correlation
					# tracker     
					tracker = dlib.correlation_tracker()
					rect = dlib.rectangle(i[0], i[1], i[2], i[3])
					tracker.start_track(rgb, rect)
					trackers.append(tracker)
			# otherwise, we should utilize our object *trackers* rather than
			# object *detectors* to obtain a higher frame processing throughput
			else:
				# loop over the trackers
				for tracker in trackers:
					# set the status of our system to be 'tracking' rather
					# than 'waiting' or 'detecting'
					status = "Tracking"

					# update the tracker and grab the updated position
					tracker.update(rgb)
					pos = tracker.get_position()

					# unpack the position object
					startX = int(pos.left())
					startY = int(pos.top())
					endX = int(pos.right())
					endY = int(pos.bottom())

					# add the bounding box coordinates to the rectangles list
					rects.append((startX, startY, endX, endY))
			# draw a horizontal line in the center of the frame -- once an
			# object crosses this line we will determine whether they were
			# moving 'up' or 'down'
			trigger = None
			if self.trigger_conf == "W2":
				trigger = W // 2
				cv2.line(frame, (trigger, 0), (trigger, H), (0, 255, 255), 2)
			elif self.trigger_conf == "H2":
				trigger = H-(H//2)
				cv2.line(frame, (0, trigger), (W, trigger), (0, 255, 255), 2)
			objects = ct.update(rects)

			# loop over the tracked objects to detect whether item
			# is borrowed or returned 
			for (objectID, centroid) in objects.items():
				# check to see if a trackable object exists for the current
				# object ID
				object_ID_s = object_ID
				to = trackableObjects.get(objectID, None)

				# if there is no existing trackable object, create one
				if to is None:					
					to = TrackableObject(objectID, centroid)
					flag_justcreated = True
								

				# otherwise, there is a trackable object so we can utilize it
				# to determine direction
				else:
					if flag_justcreated is True:
						flag_justcreated = False
						
					# the difference between the y-coordinate of the *current*
					# centroid and the mean of *previous* centroids will tell
					# us in which direction the object is moving (negative for
					# 'up' and positive for 'down')
					y = [c[1] for c in to.centroids]
					direction = centroid[0] - np.mean(y)
					to.centroids.append(centroid)               
					# print(direction)
					# ~ print(str(direction)+" "+str(centroid[0]))

					# check to see if the object has been counted or not
					# passed is for checking whether the object has passed
					# the trigger line. 0 - False, 1 - True 
					if passed == 0 and (centroid[0] in range(trigger-5,trigger+5)):
						# set passed to 1 if object enters trigger line
						# to go through the next conditional statements
						# then skip for loop to next iteration
						# if this isn't skipped, the following 
						# conditional statements won't activate
						passed = 1
						# print("passed")
						continue
					if passed == 1 and not to.counted:
						# if the direction is negative (indicating the object
						# is moving up) AND the centroid is above the center
						# line, count the object
						# NOTE: passed is assigned 0 again which if
						# if the object passes the trigger line again,
						# in the next couple of frames, we can
						# go back to this statement via setting
						# to.counted to false in the next
						# statement  
						to.counted = True
						datetime = dt.now()
						passed = 0
						object_ID = objectID
						item_stat_f = None
						if direction < 0 and centroid[0] < trigger:
							totalUp += 1
							item_stat = "Returned"
							item_stat_f = 0
							# print("objectID:"+str(object_ID)+" date:"+str(datetime)+" stat:"+
							# 		str(item_stat))
						# if the direction is positive (indicating the object
						# is moving down) AND the centroid is below the
						# center line, count the object
						elif direction > 0 and centroid[0] > trigger:
							totalDown += 1							
							item_stat = "Borrowed"
							item_stat_f = 1
							# print("objectID:"+str(object_ID)+" date:"+str(datetime)+" stat:"+
							# 		str(item_stat))
						#NOTICE: 1 in the dictionary here is the ID number of projector in database 
						to_save_list[object_ID] = (1,datetime,item_stat_f)
						flag_idchanged = True
						flag_reset = False
						# print(to_save_list)
					elif passed == 1 and to.counted:											
						to.counted = False					
					elif (passed == 0 and not to.counted) and not flag_justcreated:
						flag_idchanged = False
					# elif (passed == 0 and not to.counted) and flag_idchanged is None:

					# elif (passed == 0 and not to.counted) and flag_idchanged:
					# 	flag_reset = True
						# print("passed status:"+str(passed)+
						# 	" to.counted status:"+str(to.counted))

				
				trackableObjects[objectID] = to
				# draw both the ID of the object and the centroid of the
				# object on the output frame
				text = "ID {}".format(objectID)
				cv2.rectangle(frame, (startX, startY), (endX, endY),
							(0, 255, 0), 2)
				cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
				cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)
			
			
			
			# construct a tuple of information we will be displaying on the
			# frame
			info = [
				("ID", object_ID),
				("DateTime", datetime),
				("Item_Stat", item_stat),
				("Status", status),
			]
			for (i, (k, v)) in enumerate(info):
				text = "{}: {}".format(k, v)
				cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
			# output_frames.append(frame)
			totalFrames += 1
			fps.update()
			output = None
			# For Database Update
			# If objects is empty and there is something to_save
			# NOTES: Move this if statement to app.py
			# Processing of saving to database shall be
			# done there. Compare the save_list of two instances
			# in order to know whether insert it to database or 
			# not
			#  
			# print(to_save_list)
			# output = {"frame":frame,"list": to_save_list, "centroid":ct}
			# yield output
			if (flag_justcreated):
				flag_reset = None
				flag_idchanged = None
			elif (flag_idchanged is not None and not flag_idchanged) and (
				ct.nextObjectID > object_ID):
				flag_reset = True
				flag_idchanged = None	
			
			if(flag_reset is None):
				output = {"frame":frame,"list": to_save_list.copy(), "centroid": ct, "objectID":object_ID}
				yield output
			elif(not flag_reset):
				# #INSERT TO DATABASE HERE. CREATE A CLASS for handling mySQL queries
				output = {"frame":frame,"list": to_save_list.copy(), "centroid":ct, "objectID":object_ID}
				yield output
				del to_save_list[object_ID_s]
				print("flagidchanged state:")
				print(flag_idchanged)
				print("flagreset state:")
				print(flag_reset)
				flag_reset = None
				flag_idchanged = None
				ct.reset(object_ID_s+1)

			# Change how to reset APril 14, 2021
			elif(flag_reset):
				output = {"frame":frame,"list": to_save_list.copy(), "centroid":ct, "objectID":object_ID}
				yield output
				ct.reset(object_ID_s)
				print("2flagidchanged state:")
				print(flag_idchanged)
				print("2flagreset state:")
				print(flag_reset)
				flag_reset = None
				# for objectID in list(to_save_list.keys()):
				# 	# print("here")				
				# 	# status = None
				# 	# camdb = None
				# 	# if camera == "pi":
				# 	# 	camdb = 1
				# 	# elif camera == "webcam":
				# 	# 	camdb = 2
				# 	# if to_save_list[objectID][2]==0:
				# 	# 	status = "returned"
				# 	# elif to_save_list[objectID][2]==1:
				# 	# 	status = "borrowed"
				# 	# db.insert(idInventory=to_save_list[objectID][0],
				# 	# 			date=to_save_list[objectID][1],camera=camdb,nametable=status)					
				# 	# print("StreamController if before:")
				# 	# print(to_save_list)
				# 	print(objectID)
					
				# 	print("StreamController if before:")
				# 	print(to_save_list)
			# elif ((objects is not None) and (bool(objects))) and not bool(to_save_list):
			# # 	# print("secondif")
			# # 	# print(objects)
			# # 	output = {"frame":frame,"list": to_save_list.copy(), "centroid": None}
			# # 	yield output
			# 	ct.reset(object_ID)
			# 	# objects = None

				
			