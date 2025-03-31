
import cv2
import numpy as np
from multiprocessing import shared_memory
import logging
import helper_functions as HF

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
)

def clean_up_resources_and_exit(cap, shm, shared_dict):
    shared_dict["stop"] = True
    cap.release()
    shm.close()
    # shm.unlink()
    logging.warning("Capture process is done.")
    exit()

def capture_frames_main(video_path, shm_name, frame_shape, shared_dict, event_dict):
    try:
        cap = HF.assign_cap_base_on_os(video_path)
    except Exception as e:
        logging.error(f"Error: {e}")
        shared_dict["stop"] = True
        exit()

    shm = shared_memory.SharedMemory(name=shm_name, create=False)
    shared_frame = np.ndarray(frame_shape, dtype=np.uint8, buffer=shm.buf)

    if not cap.isOpened():
        logging.error("Error: Cannot open video.")
        clean_up_resources_and_exit(cap, shm, shared_dict)
        # shared_dict["stop"] = True
        # exit()

    event_dict["create_other_processes"].set() # Signal the main process that p1 has started

    while cap.isOpened() and not shared_dict["stop"]:
        ret, frame = cap.read()
        if not ret:
            logging.error("Error: Cannot read the video.")
            shared_dict["stop"] = True
            break

        np.copyto(shared_frame, frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            shared_dict["stop"] = True
            break

    logging.warning("Capture process is done.")
    # exit()
    clean_up_resources_and_exit(cap, shm, shared_dict)
    exit()
