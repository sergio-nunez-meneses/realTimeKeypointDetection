import cv2 as cv
import time
import os

from threading import Thread
from datetime import datetime


class VideoStream:
	def __init__(self, source):
		self.source = source
		self.cap = cv.VideoCapture(self.source)

		if not self.cap.isOpened():
			print("Error accessing webcam stream")
			exit(1)

		# Read single frame from stream for initialization
		self.ret, self.frame = self.cap.read()
		if not self.ret:
			print("No more frames to read")
			exit(1)

		self.source_is_live = not isinstance(self.source, str)

		self.fps = None if self.source_is_live else 1 / int(self.cap.get(cv.CAP_PROP_FPS))
		self.fps_to_ms = 1 if self.source_is_live else int(self.fps * 1000)

		self.is_recording = False
		self.record = False
		self.writer = None

		self.stopped = True

		self.t = Thread(target=self.update, args=())
		self.t.daemon = True

	def start(self):
		self.stopped = False
		self.t.start()

	def update(self):
		while True:
			if self.stopped:
				break

			self.ret, self.frame = self.cap.read()

			if not self.ret:
				self.cap.set(cv.CAP_PROP_POS_FRAMES, 0)
				continue

			if not self.source_is_live:
				time.sleep(self.fps)
		self.cap.release()

	def read(self):
		return self.frame

	def stop(self):
		self.stopped = True

	def set_record(self):
		path = os.path.abspath(os.getcwd())
		now = datetime.today().strftime("%Y%m%d%H%M%S")
		filename = f"{path}/output_data/output_{now}.mp4"

		self.writer = cv.VideoWriter(filename, cv.VideoWriter_fourcc(*"mp4v"), int(self.cap.get(cv.CAP_PROP_FPS)),
		                             (int(self.cap.get(cv.CAP_PROP_FRAME_WIDTH)),
		                              int(self.cap.get(cv.CAP_PROP_FRAME_HEIGHT))))
		self.record = True

	def handle_record(self, stream, udp):
		if self.record:
			self.is_recording = True

		if self.record and self.is_recording:
			self.writer.write(cv.flip(stream, 1))
			print("Recording...")

			udp.send("/record", True)
		elif not self.record and self.is_recording:
			udp.send("/record", False)

			self.writer.release()
			print("Recording stopped")

			self.is_recording = False

	def stop_record(self):
		self.record = False
