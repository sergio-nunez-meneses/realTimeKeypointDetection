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
		self.landmarks = {
			"left_hand":  None,
			"right_hand": None
		}

		self.solution = mp.solutions
		self.inference = self.solution.holistic.Holistic(min_detection_confidence=min_detection_confidence,
		                                                 min_tracking_confidence=min_tracking_confidence)
		self.drawing = self.solution.drawing_utils
		self.drawing_styles = self.solution.drawing_styles

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
			visible_address = "{}/visible".format(base_address)

			# Get coordinates from landmarks
			if self.landmarks[hand_name] is not None:
				udp.send(visible_address, True)

				for y in range(len(self.named_hand_landmarks)):
					landmark_name = self.named_hand_landmarks[y]

					if landmark_name in self.landmarks_to_render:
						landmark_data = self.landmarks[hand_name].landmark[y]

						x = scale_to_range(landmark_data.x, [1, 0], [0, 1]),
						y = landmark_data.y,
						raw_z = landmark_data.z
						z = raw_z * (10 ** count_zeros(raw_z))
						z = z if landmark_name == "wrist" else scale_to_range(z, [0, -1], [0, 1])
						hand_data = [x[0], y[0], z]

						landmark_address = "{}/{}/xyz".format(base_address, landmark_name)
						udp.send(landmark_address, hand_data)

				# Draw landmarks
				self.drawing.draw_landmarks(
					self.image,
					self.landmarks[hand_name],
					self.solution.holistic.HAND_CONNECTIONS,
					self.drawing_styles.get_default_hand_landmarks_style(),
					self.drawing_styles.get_default_hand_connections_style()
				)
			else:
				udp.send(visible_address, False)


def scale_to_range(value, min, max):
	return (value - min[0]) * (max[1] - max[0]) / (min[1] - min[0]) + max[0]


def count_zeros(decimal):
	return inf if decimal == 0 else -floor(log10(abs(decimal))) - 1
