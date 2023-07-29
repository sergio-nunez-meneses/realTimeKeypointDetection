import tensorflow as tf
import mediapipe as mp
import cv2 as cv


if __name__ == "__main__":
    if len(tf.config.list_physical_devices("GPU")) > 0:
        cap = cv.VideoCapture(0)
        if not cap.isOpened():
            print("Error accessing webcam stream.")
            exit(1)

        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        mp_holistic = mp.solutions.holistic

        with mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as holistic:
            while True:
                ret, frame = cap.read()

                if not ret:
                    print("No more frames to read.")
                    continue

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

                cv.imshow("Real-time keypoint detection", cv.flip(image, 1))

                if cv.waitKey(1) == 27:
                    break

            cap.release()
            cv.destroyAllWindows()
    else:
        print("MPS GPU is not available")
