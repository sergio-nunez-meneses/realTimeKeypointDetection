import tensorflow as tf
import mediapipe as mp
import cv2 as cv
import time

from threading import Thread


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


if __name__ == "__main__":
    if len(tf.config.list_physical_devices("GPU")) > 0:
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
                    for i in range(len(hand_landmarks)):
                        landmark_name = hand_landmarks[i]

                        if landmark_name in allowed_landmarks:
                            hand_data = {
                                landmark_name: {
                                    "i": i + 1,
                                    "x": left_hand.landmark[i].x,
                                    "y": left_hand.landmark[i].y,
                                    "z": left_hand.landmark[i].z
                                }
                            }
                            # print("Left {0}: ".format(" ".join(landmark_name.split("_"))), hand_data[landmark_name])
                if right_hand:
                    for i in range(len(hand_landmarks)):
                        landmark_name = hand_landmarks[i]

                        if landmark_name in allowed_landmarks:
                            hand_data = {
                                landmark_name: {
                                    "index": i + 1,
                                    "x":     right_hand.landmark[i].x,
                                    "y":     right_hand.landmark[i].y,
                                    "z":     right_hand.landmark[i].z
                                }
                            }
                            # print("Right {0}: ".format(" ".join(landmark_name.split("_"))), hand_data[landmark_name])

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
