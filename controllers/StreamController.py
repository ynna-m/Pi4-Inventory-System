# USAGE
# To read and write back out to video:
# python people_counter.py --prototxt mobilenet_ssd/MobileNetSSD_deploy.prototxt \
#   --model mobilenet_ssd/MobileNetSSD_deploy.caffemodel --input videos/example_01.mp4 \
#   --output output/output_01.avi
#
# To read from webcam and write back out to disk:
# python people_counter.py --prototxt mobilenet_ssd/MobileNetSSD_deploy.prototxt \
#   --model mobilenet_ssd/MobileNetSSD_deploy.caffemodel \
#   --output output/webcam_output.avi

# import the necessary packages
from packages.pyimagesearch.centroidtracker import CentroidTracker
from packages.pyimagesearch.trackableobject import TrackableObject
from packages.thesisdatabase.mysql_inventory import InventoryRepository
from imutils.video import VideoStream
from imutils.video import FPS
from datetime import datetime as dt
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2

class StreamController:
	
	def __init__(self, model, config):
		self.model=model
		self.config=config
	# Malisiewicz et al.
	def non_max_suppression_fast(self, boxes, overlapThresh):
		# if there are no boxes, return an empty list
		# print(boxes)
		if boxes is None:
			return []
		if len(boxes) == 0:
			return []

		# if the bounding boxes integers, convert them to floats --
		# this is important since we'll be doing a bunch of divisions
		if boxes.dtype.kind == "i":
			boxes = boxes.astype("float")

		# initialize the list of picked indexes 
		pick = []

		# grab the coordinates of the bounding boxes
		x1 = boxes[:,0]
		y1 = boxes[:,1]
		x2 = boxes[:,2]
		y2 = boxes[:,3]

		# compute the area of the bounding boxes and sort the bounding
		# boxes by the bottom-right y-coordinate of the bounding box
		area = (x2 - x1 + 1) * (y2 - y1 + 1)
		idxs = np.argsort(y2)

		# keep looping while some indexes still remain in the indexes
		# list
		while len(idxs) > 0:
			# grab the last index in the indexes list and add the
			# index value to the list of picked indexes
			last = len(idxs) - 1
			i = idxs[last]
			pick.append(i)

			# find the largest (x, y) coordinates for the start of
			# the bounding box and the smallest (x, y) coordinates
			# for the end of the bounding box
			xx1 = np.maximum(x1[i], x1[idxs[:last]])
			yy1 = np.maximum(y1[i], y1[idxs[:last]])
			xx2 = np.minimum(x2[i], x2[idxs[:last]])
			yy2 = np.minimum(y2[i], y2[idxs[:last]])

			# compute the width and height of the bounding box
			w = np.maximum(0, xx2 - xx1 + 1)
			h = np.maximum(0, yy2 - yy1 + 1)

			# compute the ratio of overlap
			overlap = (w * h) / area[idxs[:last]]

			# delete all indexes from the index list that have
			idxs = np.delete(idxs, np.concatenate(([last],
				np.where(overlap > overlapThresh)[0])))

		# return only the bounding boxes that were picked using the
		# integer data type
		return boxes[pick].astype("int")
	def stream(self):
		# initialize the list of class labels MobileNet SSD was trained to
		# detect
		model=self.model
		config=self.config
		# construct the argument parse and parse the arguments
		ap = argparse.ArgumentParser()
		# ap.add_argument("-p", "--pbtxt", required=True,
		# 	help="path to 'deploy' config file")
		# ap.add_argument("-m", "--model", required=True,
		# 	help="path to pre-trained model")
		ap.add_argument("-i", "--input", type=str,
			help="path to optional input video file")
		ap.add_argument("-o", "--output", type=str,
			help="path to optional output video file")
		ap.add_argument("-c", "--confidence", type=float, default=0.80,
			help="minimum probability to filter weak detections")
		ap.add_argument("-s", "--skip-frames", type=int, default=25,
			help="# of skip frames between detections")
		args = vars(ap.parse_args())
		CLASSES = ["none","projector"]
		db = InventoryRepository()
		# load our serialized model from disk
		print("[INFO] loading model...")
		net = cv2.dnn.readNet(model=model, config=config)
		net0 = cv2.dnn.readNet(model=model, config=config)
		net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
		net0.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
		# if a video path was not supplied, grab a reference to the webcam
		if not args.get("input", False):
			print("[INFO] starting video stream...")
			vs = VideoStream(usePiCamera=True).start()
			vs0 = VideoStream(src=0).start()
			time.sleep(2.0)

		# otherwise, grab a reference to the video file
		else:
			print("[INFO] opening video file...")
			vs = cv2.VideoCapture(args["input"])

		# initialize the video writer (we'll instantiate later if need be)
		writer = None

		# initialize the frame dimensions (we'll set them as soon as we read
		# the first frame from the video)
		W = None
		H = None

		# instantiate our centroid tracker, then initialize a list to store
		# each of our dlib correlation trackers, followed by a dictionary to
		# map each unique object ID to a TrackableObject

		ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
		ct0 = CentroidTracker(maxDisappeared=40, maxDistance=50)
		trackers = []
		trackableObjects = {}
		trackers0 = []
		trackableObjects0 = {}
		# initialize the total number of frames processed thus far, along
		# with the total number of objects that have moved either up or down
		totalFrames = 0
		totalDown = 0
		totalUp = 0
		totalDown0 = 0
		totalUp0 = 0
		passed = 0 # event trigger0
		passed0 = 0 # event trigger0
		object_ID = 0
		object_ID0 = 0
		datetime = ""
		datetime0 = ""
		item_stat = ""
		item_stat0 = ""
		to_save_list = {} #final saving for database insertion for 1st camera
		to_save_list0 = {} #for second camera
		
		# start the frames per second throughput estimator
		fps = FPS().start()
		
		# loop over frames from the video stream
		while True:
			output_frames = []
			response = False
			# grab the next frame and handle if we are reading from either
			# VideoCapture or VideoStream
			frame = vs.read()
			frame = frame[1] if args.get("input", False) else frame
			frame0 = vs0.read()
			
			# if we are viewing a video and we did not grab a frame then we
			# have reached the end of the video
			if args["input"] is not None and frame is None:
				break

			# resize the frame to have a maximum width of 500 pixels (the
			# less data we have, the faster we can process it), then convert
			# the frame from BGR to RGB for dlib
			frame = imutils.resize(frame, width=300)
			frame0 = imutils.resize(frame0, width=300)
			rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			rgb0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2RGB)
			# if the frame dimensions are empty, set them
			if W is None or H is None:
				(H, W) = frame.shape[:2]
				(H0, W0) = frame0.shape[:2]

			# if we are supposed to be writing a video to disk, initialize
			# the writer
			if args["output"] is not None and writer is None:
				fourcc = cv2.VideoWriter_fourcc(*"MJPG")
				writer = cv2.VideoWriter(args["output"], fourcc, 30,
					(W, H), True)

			# initialize the current status along with our list of bounding
			# box rectangles returned by either (1) our object detector or
			# (2) the correlation trackers
			status = "Waiting"
			rects = []
			rects0 = []
			# check to see if we should run a more computationally expensive
			# object detection method to aid our tracker
			# if len(trackers)==0:
			if totalFrames % args["skip_frames"] == 0:
				# set the status and initialize our new set of object trackers
				status = "Detecting"
				trackers = []
				trackers0 = []
				# convert the frame to a blob and pass the blob through the
				# network and obtain the detections
				blob = cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False)
				blob0 = cv2.dnn.blobFromImage(frame0,size=(300, 225), swapRB=True, crop=False)
				net.setInput(blob)
				net0.setInput(blob0)
				detections = net.forward()
				detections0 = net0.forward()
				rectangles = []
				rectangles0 = []
				# loop over the detections
				for i in np.arange(0, detections.shape[2]):
					# extract the confidence (i.e., probability) associated
					# with the prediction           
					confidence = detections[0, 0, i, 2]
					# filter out weak detections by requiring a minimum
					# confidence
					if confidence > args["confidence"]:
						# extract the index of the class label from the
						# detections list
						# [0, 0, i, 1] = index of class label
						# [0, 0, i, 2] = confidence in decimal
						# [0, 0, i, 3:7(or 3-6)] = bounding box coordinates

						idx = int(detections[0, 0, i, 1])
						
						# if the class label is not a person, ignore it
						if CLASSES[idx] != "projector":
							continue

						# compute the (x, y)-coordinates of the bounding box
						# for the object
						box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
						(startX, startY, endX, endY) = box.astype("int")
						
						rectangles.append((startX,startY,endX,endY))                       
				rectboxes = np.array(rectangles,dtype="float64")
				nms = self.non_max_suppression_fast(rectboxes,0.03) # Remove Extra Detections
				for i in nms:               
					# construct a dlib rectangle object from the bounding
					# box coordinates and then start the dlib correlation
					# tracker     
					tracker = dlib.correlation_tracker()
					rect = dlib.rectangle(i[0], i[1], i[2], i[3])
					tracker.start_track(rgb, rect)
					trackers.append(tracker)
				# loop over the detections
				for i in np.arange(0, detections0.shape[2]):
					# extract the confidence (i.e., probability) associated
					# with the prediction           
					confidence0 = detections0[0, 0, i, 2]
					# filter out weak detections by requiring a minimum
					# confidence
					if confidence0 > args["confidence"]:
						# extract the index of the class label from the
						# detections list
						# [0, 0, i, 1] = index of class label
						# [0, 0, i, 2] = confidence in decimal
						# [0, 0, i, 3:7(or 3-6)] = bounding box coordinates

						idx0 = int(detections0[0, 0, i, 1])
						
						# if the class label is not a person, ignore it
						if CLASSES[idx0] != "projector":
							continue

						# compute the (x, y)-coordinates of the bounding box
						# for the object
						box0 = detections0[0, 0, i, 3:7] * np.array([W0, H0, W0, H0])
						(startX0, startY0, endX0, endY0) = box0.astype("int")
						
						rectangles0.append((startX0,startY0,endX0,endY0))                       
				rectboxes0 = np.array(rectangles0,dtype="float64")
				nms0 = self.non_max_suppression_fast(rectboxes0,0.03) # Remove Extra Detections
				for i in nms0:               
					# construct a dlib rectangle object from the bounding
					# box coordinates and then start the dlib correlation
					# tracker     
					tracker0 = dlib.correlation_tracker()
					rect0 = dlib.rectangle(i[0], i[1], i[2], i[3])
					tracker0.start_track(rgb0, rect0)
					trackers0.append(tracker0)                 
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
				# loop over the trackers
				for tracker0 in trackers0:
					# set the status of our system to be 'tracking' rather
					# than 'waiting' or 'detecting'
					status = "Tracking"

					# update the tracker and grab the updated position
					tracker0.update(rgb0)
					pos0 = tracker0.get_position()

					# unpack the position object
					startX0 = int(pos0.left())
					startY0 = int(pos0.top())
					endX0 = int(pos0.right())
					endY0 = int(pos0.bottom())

					# add the bounding box coordinates to the rectangles list
					rects0.append((startX0, startY0, endX0, endY0))
			# draw a horizontal line in the center of the frame -- once an
			# object crosses this line we will determine whether they were
			# moving 'up' or 'down'
			trigger = W // 2
			trigger0 = H-(H-85)
			cv2.line(frame, (trigger, 0), (trigger, H), (0, 255, 255), 2)
			cv2.line(frame0, (0, trigger0), (W0 , trigger0), (0, 255, 255), 2)
			# use the centroid tracker to associate the (1) old object
			# centroids with (2) the newly computed object centroids
			objects = ct.update(rects)
			objects0 = ct0.update(rects0)

			# For Database Update
			# If objects is empty and there is something to_save
			if (not objects) and to_save_list:
				#INSERT TO DATABASE HERE. CREATE A CLASS for handling mySQL queries
				#CAMERA 1
				for objectID in list(to_save_list.keys()):
					status = None
					if to_save_list[objectID][2]==0:
						status = "returned"
					elif to_save_list[objectID][2]==1:
						status = "borrowed"
					db.insert(idInventory=to_save_list[objectID][0],
								date=to_save_list[objectID][1],camera=1,nametable=status)
					del to_save_list[objectID]
					
				print(to_save_list)
			if (not objects0) and to_save_list0:
				#INSERT TO DATABASE HERE. CREATE A CLASS for handling mySQL queries
				#CAMERA 2
				for objectID in list(to_save_list0.keys()):
					status = None
					if to_save_list0[objectID][2]==0:
						status = "returned"
					elif to_save_list0[objectID][2]==1:
						status = "borrowed"
					db.insert(idInventory=to_save_list0[objectID][0],
								date=to_save_list0[objectID][1],camera=2,nametable=status)
					del to_save_list0[objectID]
				
			#add databasecontroller return then yield it to view
			#move this ^ block to a function btw
				print(to_save_list0)

			# loop over the tracked objects
			for (objectID, centroid) in objects.items():
				# check to see if a trackable object exists for the current
				# object ID
				to = trackableObjects.get(objectID, None)

				# if there is no existing trackable object, create one
				if to is None:
					to = TrackableObject(objectID, centroid)

				# otherwise, there is a trackable object so we can utilize it
				# to determine direction
				else:
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
					if passed == 0 and (centroid[0] in range(trigger-5,trigger+5)):
						passed = 1
						print("passed")
						continue
					if passed == 1 and not to.counted:
						# if the direction is negative (indicating the object
						# is moving up) AND the centroid is above the center
						# line, count the object
						if direction < 0 and centroid[0] < trigger:
							totalUp += 1
							to.counted = True
							datetime = dt.now()
							item_stat = "Returned"
							item_stat_f = 0
							passed = 0
							previousdirection = direction
							object_ID = objectID
							print("objectID:"+str(object_ID)+" date:"+str(datetime)+" stat:"+
									str(item_stat))
							#NOTICE: 1 in the dictionary here is the ID number of projector in database 
							to_save_list[object_ID] = (1,datetime,item_stat_f)
							print(to_save_list)
						# if the direction is positive (indicating the object
						# is moving down) AND the centroid is below the
						# center line, count the object
						elif direction > 0 and centroid[0] > trigger:
							totalDown += 1
							to.counted = True
							datetime = dt.now()
							# print("dir:"+str(direction)+" cent:"+str(centroid[1]))
							item_stat = "Borrowed"
							item_stat_f = 1
							passed = 0
							previousdirection = direction
							object_ID = objectID
							print("objectID:"+str(object_ID)+" date:"+str(datetime)+" stat:"+
									str(item_stat))
							#NOTICE: 1 in the dictionary here is the ID number of projector in database
							to_save_list[object_ID] = (1,datetime,item_stat_f)
							print(to_save_list)
					elif passed == 1 and to.counted:
						to.counted = False
				trackableObjects[objectID] = to
				# draw both the ID of the object and the centroid of the
				# object on the output frame
				text = "ID {}".format(objectID)
				cv2.rectangle(frame, (startX, startY), (endX, endY),
							(0, 255, 0), 2)
				cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
				cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)
				# ~ if totalFrames % (args["skip_frames"] - 1) == 0:
					# ~ pf_frame = (startX, startY, endX, endY)
			for (objectID0, centroid0) in objects0.items():
				# check to see if a trackable object exists for the current
				# object ID
				to0 = trackableObjects0.get(objectID0, None)

				# if there is no existing trackable object, create one
				if to0 is None:
					to0 = TrackableObject(objectID0, centroid0)

				# otherwise, there is a trackable object so we can utilize it
				# to determine direction
				else:
					# the difference between the y-coordinate of the *current*
					# centroid and the mean of *previous* centroids will tell
					# us in which direction the object is moving (negative for
					# 'up' and positive for 'down')
					y = [c[1] for c in to0.centroids]
					direction = centroid0[1] - np.mean(y)
					to0.centroids.append(centroid0)               
					# print(direction)
					# ~ print(str(direction)+" "+str(centroid[0]))
					# check to see if the object has been counted or not
					if passed0 == 0 and (centroid0[1] in range(trigger0-5,trigger0+5)):
						passed0 = 1
						print("passed0")
						continue
					if passed0 == 1 and not to0.counted:
						# if the direction is negative (indicating the object
						# is moving up) AND the centroid is above the center
						# line, count the object
						if direction < 0 and centroid0[1] < trigger0:
							totalUp0 += 1
							to0.counted = True
							datetime0 = dt.now()
							item_stat0 = "Returned"
							item_stat_f0 = 0
							passed0 = 0
							previousdirection0 = direction
							object_ID0 = objectID0
							print("objectID:"+str(object_ID0)+" date:"+str(datetime0)+" stat:"+
									str(item_stat0))
							#NOTICE: 1 in the dictionary here is the ID number of projector in database 
							to_save_list0[object_ID0] = (1,datetime0,item_stat_f0)
							print(to_save_list0)
						# if the direction is positive (indicating the object
						# is moving down) AND the centroid is below the
						# center line, count the object
						elif direction > 0 and centroid0[1] > trigger0:
							totalDown0 += 1
							to0.counted = True
							datetime0 = dt.now()
							# print("dir:"+str(direction)+" cent:"+str(centroid[1]))
							item_stat0 = "Borrowed"
							item_stat_f0 = 1
							passed0 = 0
							previousdirection0 = direction
							object_ID0 = objectID0
							print("objectID:"+str(object_ID0)+" date:"+str(datetime0)+" stat:"+
									str(item_stat0))
							#NOTICE: 1 in the dictionary here is the ID number of projector in database
							to_save_list0[object_ID0] = (1,datetime0,item_stat_f0)
							print(to_save_list0)
					elif passed0 == 1 and to0.counted:
						to0.counted = False
				# store the trackable object in our dictionary
				trackableObjects0[objectID0] = to0
				# draw both the ID of the object and the centroid of the
				# object on the output frame
				text = "ID {}".format(objectID0)
				cv2.rectangle(frame0, (startX0, startY0), (endX0, endY0),
							(0, 255, 0), 2)
				cv2.putText(frame0, text, (centroid0[0] - 10, centroid0[1] - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
				cv2.circle(frame0, (centroid0[0], centroid0[1]), 4, (0, 255, 0), -1)
				# ~ if totalFrames % (args["skip_frames"] - 1) == 0:
					# ~ pf_frame = (startX, startY, endX, endY)

			# construct a tuple of information we will be displaying on the
			# frame
			# info = [
			#     ("Left", totalUp),
			#     ("Right", totalDown),
			#     ("Status", status),
			# ]
			# info0 = [
			#     ("Up", totalUp0),
			#     ("Down", totalDown0),
			#     ("Status", status),
			# ]
			info = [
				("ID", object_ID),
				("DateTime", datetime),
				("Item_Stat", item_stat),
				("Status", status),
			]
			info0 = [
				("ID", object_ID0),
				("DateTime", datetime0),
				("Item_Stat", item_stat0),
				("Status", status),
			]
			# loop over the info tuples and draw them on our frame
			for (i, (k, v)) in enumerate(info):
				text = "{}: {}".format(k, v)
				cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
			for (i, (k, v)) in enumerate(info0):
				text = "{}: {}".format(k, v)
				cv2.putText(frame0, text, (10, H - ((i * 20) + 20)),
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
			# check to see if we should write the frame to disk
			if writer is not None:
				writer.write(frame)

			# show the output frame
			# cv2.imshow("Frame", frame)
			# cv2.imshow("Frame0", frame0)
			# key = cv2.waitKey(1) & 0xFF

			# if the `q` key was pressed, break from the loop
			# if key == ord("q"):
			# 	break

			# increment the total number of frames processed thus far and
			# then update the FPS counter
			totalFrames += 1
			fps.update()
			output_frames.append(frame)
			output_frames.append(frame0)
			yield output_frames
			# yield ({"frame":frame,"frame0":frame0})

		# # stop the timer and display FPS information
		# fps.stop()
		# print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
		# print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

		# # check to see if we need to release the video writer pointer
		# if writer is not None:
		# 	writer.release()

		# # if we are not using a video file, stop the camera video stream
		# if not args.get("input", False):
		# 	vs.stop()

		# # otherwise, release the video file pointer
		# else:
		# 	vs.release()

		# # close any open windows
		# cv2.destroyAllWindows()

	def encodejpg(self,frame):
		return cv2.imencode(".jpg", frame)
	

# if __name__ == "__main__":
# 	main()

