import cv2
import numpy as np
from multiprocessing import shared_memory
from .motion_detector import MotionDetector

def motion_detection_main(shm_name, frame_shape, shared_dict, barrier_dict):
    try:
        shm = shared_memory.SharedMemory(name=shm_name, create=False)
        shared_frame = np.ndarray(frame_shape, dtype=np.uint8, buffer=shm.buf)
        motion_detector = MotionDetector()
        motion_detector.setup(shared_frame, size=350)
        motion_detector.initialize_model(shared_frame)
        barrier_dict["MD_OD"].wait()
        while not shared_dict["stop"]:
            shared_dict["motion_detected"] = motion_detector.detect_motion_with_threshold(shared_frame, 
                                                                                          motion_detected_threshold=1, 
                                                                                          visualize = True)
            # Break the loop if 'q' is pressed
            if cv2.waitKey(10) & 0xFF == ord('q'):
                shared_dict["stop"] = True
                break
        shm.close()
        print("Motion detection process is done.")
        exit()
    except FileNotFoundError:
        print(f"Shared memory '{shm_name}' does not exist.")
        shared_dict["stop"] = True
        exit()



