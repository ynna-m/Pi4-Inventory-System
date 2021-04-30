from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import time
import cv2
import base64
class StreamTestController:
	def __init__(self, model, config):
		self.model=model
		self.config=config
	def stream(self):
		model = self.model
		config = self.config
		ap = argparse.ArgumentParser()
		# ap.add_argument("-p", "--pbtxt", required=True,
		# 	help="path to Tensorflow 'deploy' pbtxt file")
		# ap.add_argument("-m", "--model", required=True,
		# 	help="path to Tensorflow pre-trained model")
		ap.add_argument("-c", "--confidence", type=float, default=0.75,
			help="minimum probability to filter weak detections")
		args = vars(ap.parse_args())

		CLASSES = ["projector"]

		COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

		print("[INFO] loading model...")
		net = cv2.dnn.readNet(model=model, config=config)
		net0 = cv2.dnn.readNet(model=model, config=config)
		net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
		net0.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
		print("[INFO] starting video stream...")
		vs = VideoStream(usePiCamera=True).start()
		vs0 = VideoStream(src=1).start()
		time.sleep(2.0)
		# fps = FPS().start()

		# loop over the frames from the video stream
		while True:
			# grab the frame0 from the threaded video stream and resize it
			# to have a maximum width of 400 pixels
			frames = []
			for (stream,net) in zip((vs,vs0),(net,net0)):
				frame = stream.read()
				# grab the frame0 dimensions and convert it to a blob
				# ~ if stream.read() is None:
					
					# ~ frame = np.zeros(shape=[300,300,3], dtype=np.uint8)
				# ~ else:
								
					# ~ frame = stream.read()
				frame = imutils.resize(frame, width=300)
				(h, w) = frame.shape[:2]

				blob = cv2.dnn.blobFromImage(frame,
					size=(300, 225), swapRB=True, crop=False)

				# pass the blob through the network and obtain the detections and
				# predictions
				net.setInput(blob)
				detections = net.forward()	
					# loop over the detections
				# print(detections.shape)
				for i in np.arange(0, detections.shape[2]):
					# extract the confidence (i.e., probability) associated with
					# the prediction
					confidence = detections[0, 0, i, 2]

					if confidence > args["confidence"]:
						# extract the index of the class label from the
						# `detections`, then compute the (x, y)-coordinates of
						# the bounding box for the object
						idx = int(detections[0, 0, i, 0])
						box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
						(startX, startY, endX, endY) = box.astype("int")
				
						# draw the prediction on the frame
						label = "{}: {:.2f}%".format(CLASSES[idx],
							confidence * 100)
						cv2.rectangle(frame, (startX, startY), (endX, endY),
							COLORS[idx], 2)
						y = startY - 15 if startY - 15 > 15 else startY + 15
						cv2.putText(frame, label, (startX, y),
							cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
				frames.append(frame)
			yield frames
			# yield frames[0]
			# yield frames[1]
		# 	# show the output frame
		# 	for(frame, name) in zip(frames,("frame", "frame 0")):
		# 		cv2.imshow(name, frame)
			
		# 	key = cv2.waitKey(1) & 0xFF
		# 	# if the `q` key was pressed, break from the loop
		# 	if key == ord("q"):
		# 		break
		# 	# update the FPS counter
		# 	fps.update()
		# # stop the timer and display FPS information
		# fps.stop()
		# print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
		# print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
		# # do a bit of cleanup
		# cv2.destroyAllWindows()
		# vs.stop()
		# vs0.stop()
	def encodejpg(self,frame):
		frame = cv2.imencode(".jpg", frame)
		return frame
		
		return "data:image/jpeg;base64,{}".format(frame)
