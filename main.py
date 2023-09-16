import tensorflow as tf
import mediapipe as mp
import cv2 as cv
import time
import json
import re

from threading import Thread
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient as UDPClient
from pythonosc.osc_server import BlockingOSCUDPServer as UDPServer

from math import floor, log10, inf


class MultiThreadingVideoCapture:
	def __init__(self, source):
		self.source = source
		self.source_is_live = not isinstance(self.source, str)

		# Open video capture stream
		self.cap = cv.VideoCapture(self.source)

		if not self.cap.isOpened():
			print("Error accessing webcam stream")
			exit(1)

		# Read single frame from stream for initialization
		self.ret, self.frame = self.cap.read()
		if not self.ret:
			print("No more frames to read")
			exit(1)

		self.fps = None if self.source_is_live else 1 / int(self.cap.get(cv.CAP_PROP_FPS))
		self.fps_to_ms = 1 if self.source_is_live else int(self.fps * 1000)

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


class UDPCommunicationHandler:
	def __init__(self, ip, client_port, server_port):
		self.dispatcher = Dispatcher()

		self.ip = ip
		self.client_port = client_port
		self.server_port = server_port

		self.client = UDPClient(self.ip, self.client_port)
		self.server = UDPServer((self.ip, self.server_port), self.dispatcher)

	def send(self, address_pattern, data):
		self.client.send_message(address_pattern, data)

	# TODO: Refactor method
	def check_udp_communication(self, address_pattern):
		self.dispatcher.map(address_pattern, self.check_message_format)
		self.send(address_pattern, {"connected": False})
		self.server.handle_request()
		self.dispatcher.unmap(address_pattern, self.check_message_format)

	# TODO: Refactor method
	def check_message_format(self, address_pattern, *args):
		errors = []

		if address_pattern[1:] != "connect":
			errors.append("OSC address pattern must be /connect")

		if len(args) == 0:
			errors.append("OSC argument must not be empty")
		if len(args) > 1:
			errors.append("OSC argument must not have more than 1 element")

		message = args[0]
		if not isinstance(message, str):
			errors.append("OSC argument must be of type string")

		match = re.search("{([^}]+)}", str(message))
		if match is None:
			errors.append("OSC parsed argument must be of type JSON object")
		else:
			response = json.loads(message)

			if "errors" in response:
				print_errors(response["errors"].split(", "))

			if not isinstance(response["connected"], bool):
				errors.append("OSC parsed value must be of type boolean")

			if response["connected"]:
				print(f"Successfully communicating with UDP client through port {self.client_port}")
			else:
				errors.append("Error while communicating with UDP client through port {}".format(self.client_port))

		if len(errors) > 0:
			print_errors(errors)


class HandLandmarksHandler:
	def __init__(self, mp_solutions, min_detection_confidence, min_tracking_confidence):
		self.named_hand_landmarks = [
			"wrist", "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip", "index_finger_mcp", "index_finger_pip",
			"index_finger_dip", "index_finger_tip", "middle_finger_mcp", "middle_finger_pip", "middle_finger_dip",
			"middle_finger_tip", "ring_finger_mcp", "ring_finger_pip", "ring_finger_dip", "ring_finger_tip",
			"pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip"
		]
		self.landmarks_to_render = ["wrist", "thumb_tip", "index_finger_tip", "middle_finger_tip", "ring_finger_tip",
		                            "pinky_tip"]
		self.landmarks = {
			"left_hand":  None,
			"right_hand": None
		}

		self.holistic = mp_solutions.holistic
		self.inference = self.holistic.Holistic(min_detection_confidence=min_detection_confidence,
		                                        min_tracking_confidence=min_tracking_confidence)
		self.drawing = mp_solutions.drawing_utils
		self.drawing_styles = mp_solutions.drawing_styles

		self.image = None
		self.results = None
		self.conn = None

	def run_inference(self, frame):
		self.image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		self.image.flags.writeable = False

		self.results = self.inference.process(self.image)

		self.image.flags.writeable = True
		self.image = cv.cvtColor(self.image, cv.COLOR_RGB2BGR)

	def process_inference_data(self, udp, hand_names):
		# TODO: Refactor dict initialization
		self.landmarks["left_hand"] = self.results.left_hand_landmarks
		self.landmarks["right_hand"] = self.results.right_hand_landmarks

		for x in range(len(hand_names)):
			hand_name = hand_names[x]
			base_address = "/{}".format(hand_name)

			# Get coordinates from landmarks
			if self.landmarks[hand_name] is not None:
				# udp.send(address, {"isVisible": True})
				udp.send("{}/visible".format(base_address), True)

				for y in range(len(self.named_hand_landmarks)):
					landmark_name = self.named_hand_landmarks[y]

					if landmark_name in self.landmarks_to_render:
						landmark_data = self.landmarks[hand_name].landmark[y]
						# i = y + 1,
						x = scale_to_range(landmark_data.x, [1, 0], [0, 1]),
						y = landmark_data.y,
						raw_z = landmark_data.z
						z = raw_z * (10 ** count_zeros(raw_z))
						z = z if landmark_name == "wrist" else scale_to_range(z, [0, -1], [0, 1])

						hand_data = [x[0], y[0], z]
						udp.send("{}/{}/xyz".format(base_address, landmark_name), hand_data)

				# Draw landmarks
				self.drawing.draw_landmarks(
					self.image,
					self.landmarks[hand_name],
					self.holistic.HAND_CONNECTIONS,
					self.drawing_styles.get_default_hand_landmarks_style(),
					self.drawing_styles.get_default_hand_connections_style()
				)
			else:
				# udp.send(address, {"isVisible": False})
				udp.send("{}/visible".format(base_address), False)


def scale_to_range(value, min, max):
	return (value - min[0]) * (max[1] - max[0]) / (min[1] - min[0]) + max[0]


def count_zeros(decimal):
	return inf if decimal == 0 else -floor(log10(abs(decimal))) - 1


def print_errors(errors):
	for i in range(len(errors)):
		print(errors[i])
	exit(1)


if __name__ == "__main__":
	if len(tf.config.list_physical_devices("GPU")) > 0:
		udp = UDPCommunicationHandler("127.0.0.1", 9100, 7300)  # ip, client_port, server_port
		# udp.check_udp_communication("/connect")

		cap = MultiThreadingVideoCapture(0)
		cap.start()

		hands = HandLandmarksHandler(mp.solutions, 0.5, 0.5)

		# count_frames = 0
		# start = cv.getTickCount()

		while True:
			if cap.stopped:
				break
			else:
				frame = cap.read()

			# Get detection results
			hands.run_inference(frame)
			# Set, send, and display detection results
			hands.process_inference_data(udp, ["left_hand", "right_hand"])

			# count_frames += 1

			cv.imshow("Real-time keypoint detection", cv.flip(hands.image, 1))

			if cv.waitKey(cap.fps_to_ms) == 27:
				break
		# end = cv.getTickCount()

		cap.stop()

		# elapsed = (end - start) / cv.getTickFrequency()
		# fps = count_frames / elapsed
		# print(f"FPS: {fps:.5f}, Elapsed time: {elapsed:.5f}, Frames processed: {count_frames}")

		cv.destroyAllWindows()
	else:
		print("MPS GPU is not available")
