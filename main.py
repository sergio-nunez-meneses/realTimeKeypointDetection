import tensorflow as tf
import mediapipe as mp
import time as t
import cv2 as cv

from threading import Thread


class MultiThreadingVideoCapture:
    def __init__(self, cam_id=0):
        self.cam_id = cam_id

        # Open video capture stream
        self.cap = cv.VideoCapture(self.cam_id)
        if not self.cap.isOpened():
            print("Error accessing webcam stream.")
            exit(1)

        # Read single frame from stream for initialization
        self.ret, self.frame = self.cap.read()
        if not self.ret:
            print("No more frames to read")
            exit(1)

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
                print("No more frames to read")
                self.stopped = True
                break
        self.cap.release()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True


if __name__ == "__main__":
    if len(tf.config.list_physical_devices("GPU")) > 0:
        cap = MultiThreadingVideoCapture()
        cap.start()

        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        mp_holistic = mp.solutions.holistic

        count_frames = 0
        start = t.time()

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

                # Draw landmarks
                mp_drawing.draw_landmarks(
                    image,
                    results.left_hand_landmarks,
                    mp_holistic.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )
                mp_drawing.draw_landmarks(
                    image,
                    results.right_hand_landmarks,
                    mp_holistic.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )

                count_frames += 1

                cv.imshow("Real-time keypoint detection", cv.flip(image, 1))

                if cv.waitKey(1) == 27:
                    break
            cap.stop()

            end = t.time()
            elapsed = end - start
            fps = count_frames / elapsed
            print(f"FPS: {fps:.5f}, Elapsed time: {elapsed:.5f}, Frames processed: {count_frames}")

            cv.destroyAllWindows()
    else:
        print("MPS GPU is not available")
