import mediapipe as mp
import cv2 as cv

from math import floor, log10, inf


class Model:
	def __init__(self, min_detection_confidence, min_tracking_confidence):
		self.named_hand_landmarks = [
			"wrist", "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip", "index_finger_mcp", "index_finger_pip",
			"index_finger_dip", "index_finger_tip", "middle_finger_mcp", "middle_finger_pip", "middle_finger_dip",
			"middle_finger_tip", "ring_finger_mcp", "ring_finger_pip", "ring_finger_dip", "ring_finger_tip",
			"pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip"
		]
		self.landmarks_to_render = ["wrist", "thumb_tip", "index_finger_tip", "middle_finger_tip", "ring_finger_tip",
		                            "pinky_tip"]
		self.landmarks = {}

		self.solution = mp.solutions
		self.model = self.solution.hands.Hands(min_detection_confidence=min_detection_confidence,
				                                             min_tracking_confidence=min_tracking_confidence)
		# self.solution = mp.solutions
		# self.model = self.solution.holistic.Holistic(min_detection_confidence=min_detection_confidence,
		#                                              min_tracking_confidence=min_tracking_confidence)
		self.drawing = self.solution.drawing_utils
		self.drawing_styles = self.solution.drawing_styles

		self.image = None

	def get_data(self, frame):
		self.image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		self.image.flags.writeable = False

		results = self.model.process(self.image)

		self.image.flags.writeable = True
		self.image = cv.cvtColor(self.image, cv.COLOR_RGB2BGR)

		return results

	def process_data(self, data):
		norm_data = []

		if data.multi_hand_landmarks:
			for hand_id, hand_landmarks in enumerate(data.multi_hand_landmarks):
				hand_info = data.multi_handedness[hand_id].classification[0]

				if hand_info.score > 0.95:
					base_address = "/{}_hand".format(hand_info.label.lower())

					for landmark_id, raw_landmark_data in enumerate(hand_landmarks.landmark):
						landmark_name = self.named_hand_landmarks[landmark_id]
						landmark_address = "{}/{}/xyz".format(base_address, landmark_name)
						norm_landmark_data = {}

						if landmark_name in self.landmarks_to_render:
							norm_x = scale_to_range(raw_landmark_data.x, [1, 0], [0, 1])
							y = raw_landmark_data.y
							raw_z = raw_landmark_data.z
							z = raw_z * (10 ** count_zeros(raw_z))
							norm_z = z if landmark_name == "wrist" else scale_to_range(z, [0, -1], [0, 1])

							norm_landmark_data["address"] = landmark_address
							norm_landmark_data["value"] = [norm_x, y, norm_z]
						norm_data.append(norm_landmark_data)
		return norm_data

	@staticmethod
	def send_data(data, udp):
		if data:
			for landmark_data in data:
				if landmark_data:
					udp.send(landmark_data["address"], landmark_data["value"])

	def display_data(self):
		hand_names = list(self.landmarks.keys())

		for x in range(len(hand_names)):
			hand_name = hand_names[x]

			if self.landmarks[hand_name] is not None:
				self.drawing.draw_landmarks(
					self.image,
					self.landmarks[hand_name],
					self.solution.holistic.HAND_CONNECTIONS,
					self.drawing_styles.get_default_hand_landmarks_style(),
					self.drawing_styles.get_default_hand_connections_style()
				)


def scale_to_range(value, min, max):
	return (value - min[0]) * (max[1] - max[0]) / (min[1] - min[0]) + max[0]


def count_zeros(decimal):
	return inf if decimal == 0 else -floor(log10(abs(decimal))) - 1
