from src.video import VideoStream
from src.udp import UDP
from src.model import Model

import tensorflow as tf
import cv2 as cv


if __name__ == "__main__":
	if len(tf.config.list_physical_devices("GPU")) > 0:
		udp = UDP("127.0.0.1", 9100, 7300)

		cap = VideoStream(0)
		cap.start()

		hands = Model(0.3, 0.3)

		count_frames = 0
		start = cv.getTickCount()

		while True:
			if cap.stopped:
				break
			else:
				frame = cap.read()

			# Get detection results
			results = hands.get_data(frame)
			# Set and send detection results
			norm_data = hands.process_data(results)
			# Display detection
			# hands.display_data()

			count_frames += 1

			cap.handle_record(hands.image, udp)

			cv.imshow("Real-time keypoint detection", cv.flip(hands.image, 1))

			key = cv.waitKey(cap.fps_to_ms)
			if key == 27:
				break
			elif key == 114:
				cap.set_record()
			elif key == 115:
				cap.stop_record()
		end = cv.getTickCount()

		cap.stop()

		elapsed = (end - start) / cv.getTickFrequency()
		fps = count_frames / elapsed
		print(f"FPS: {fps:.5f}, Elapsed time: {elapsed:.5f}, Frames processed: {count_frames}")

		cv.destroyAllWindows()
	else:
		print("MPS GPU is not available")
