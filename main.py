import tensorflow as tf
import cv2 as cv


if __name__ == "__main__":
    if len(tf.config.list_physical_devices("GPU")) > 0:
        cap = cv.VideoCapture(0)
        if not cap.isOpened():
            print("Error accessing webcam stream.")
            exit(1)

        while True:
            ret, frame = cap.read()

            if not ret:
                print("No more frames to read.")
                break

            cv.imshow("Real-time keypoint detection", cv.flip(frame, 1))

            if cv.waitKey(1) == 27:
                break

        cap.release()
        cv.destroyAllWindows()
    else:
        print("MPS GPU is not available")
