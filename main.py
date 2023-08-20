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
		self.client.send_message(address_pattern, json.dumps(data))

	def check_udp_communication(self, address_pattern):
		self.dispatcher.map(address_pattern, self.check_message_format)
		self.send(address_pattern, {"connected": False})
		self.server.handle_request()
		self.dispatcher.unmap(address_pattern, self.check_message_format)

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
				self.print_errors(response["errors"].split(", "))

			if not isinstance(response["connected"], bool):
				errors.append("OSC parsed value must be of type boolean")

			if response["connected"]:
				print(f"Successfully communicating with UDP client through port {self.client_port}")
			else:
				errors.append("Error while communicating with UDP client through port {}".format(self.client_port))

		if len(errors) > 0:
			self.print_errors(errors)

	def print_errors(self, errors):
		for i in range(len(errors)):
			print(errors[i])
		exit(1)


def scale_to_range(value, min, max):
	return (value - min[0]) * (max[1] - max[0]) / (min[1] - min[0]) + max[0]


def count_zeros(decimal):
	return inf if decimal == 0 else -floor(log10(abs(decimal))) - 1


if __name__ == "__main__":
	if len(tf.config.list_physical_devices("GPU")) > 0:
		udp = UDPCommunicationHandler("127.0.0.1", 7400, 7300)  # ip, client_port, server_port
		udp.check_udp_communication("/connect")

		cap = MultiThreadingVideoCapture(0)
		cap.start()

		mp_drawing = mp.solutions.drawing_utils
		mp_drawing_styles = mp.solutions.drawing_styles
		mp_holistic = mp.solutions.holistic

		hand_landmarks = [
			"wrist", "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip", "index_finger_mcp", "index_finger_pip",
			"index_finger_dip", "index_finger_tip", "middle_finger_mcp", "middle_finger_pip", "middle_finger_dip",
			"middle_finger_tip", "ring_finger_mcp", "ring_finger_pip", "ring_finger_dip", "ring_finger_tip",
			"pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip"
		]

		allowed_landmarks = ["wrist", "thumb_tip", "index_finger_tip", "middle_finger_tip", "ring_finger_tip",
		                    "pinky_tip"]

		count_frames = 0
		start = cv.getTickCount()

		with mp_holistic.Holistic(
				min_detection_confidence=0.5,
				min_tracking_confidence=0.5
		) as holistic:
			while True:
				if cap.stopped:
					break
				else:
					frame = cap.read()

				# Get detection results
				image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
				image.flags.writeable = False

				results = holistic.process(image)

				image.flags.writeable = True
				image = cv.cvtColor(image, cv.COLOR_RGB2BGR)

				left_hand = results.left_hand_landmarks
				right_hand = results.right_hand_landmarks

				# Get coordinates from landmarks
				if left_hand:
					udp.send("/left_hand", {"isVisible": True})

					for i in range(len(hand_landmarks)):
						landmark_name = hand_landmarks[i]

						if landmark_name in allowed_landmarks:
							raw_z = left_hand.landmark[i].z
							z = raw_z * (10 ** count_zeros(raw_z))

							hand_data = {
								landmark_name: {
									"i": i + 1,
									"x": scale_to_range(left_hand.landmark[i].x, [1, 0], [0, 1]),
									"y": left_hand.landmark[i].y,
									"z": z if landmark_name == "wrist" else scale_to_range(z, [0, -1], [0, 1])
								}
							}
							udp.send("/left_hand", hand_data)
				else:
					udp.send("/left_hand", {"isVisible": False})
				if right_hand:
					udp.send("/right_hand", {"isVisible": True})

					for i in range(len(hand_landmarks)):
						landmark_name = hand_landmarks[i]

						if landmark_name in allowed_landmarks:
							raw_z = right_hand.landmark[i].z
							z = raw_z * (10 ** count_zeros(raw_z))

							hand_data = {
								landmark_name: {
									"i": i + 1,
									"x": scale_to_range(right_hand.landmark[i].x, [1, 0], [0, 1]),
									"y": right_hand.landmark[i].y,
									"z": z if landmark_name == "wrist" else scale_to_range(z, [0, -1], [0, 1])
								}
							}
							udp.send("/right_hand", hand_data)
				else:
					udp.send("/right_hand", {"isVisible": False})

				# Draw landmarks
				if left_hand:
					mp_drawing.draw_landmarks(
						image,
						left_hand,
						mp_holistic.HAND_CONNECTIONS,
						mp_drawing_styles.get_default_hand_landmarks_style(),
						mp_drawing_styles.get_default_hand_connections_style()
					)
				if right_hand:
					mp_drawing.draw_landmarks(
						image,
						right_hand,
						mp_holistic.HAND_CONNECTIONS,
						mp_drawing_styles.get_default_hand_landmarks_style(),
						mp_drawing_styles.get_default_hand_connections_style()
					)

				count_frames += 1

				cv.imshow("Real-time keypoint detection", cv.flip(image, 1))

				if cv.waitKey(cap.fps_to_ms) == 27:
					break
			end = cv.getTickCount()

			cap.stop()

			elapsed = (end - start) / cv.getTickFrequency()
			fps = count_frames / elapsed
			print(f"FPS: {fps:.5f}, Elapsed time: {elapsed:.5f}, Frames processed: {count_frames}")

			cv.destroyAllWindows()
	else:
		print("MPS GPU is not available")
