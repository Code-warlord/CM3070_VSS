import cv2
import numpy as np
from multiprocessing import Process, shared_memory, Barrier, Manager, Event
import time
from pathlib import Path
import asyncio
from collections import Counter

import capture_frame as CF
import motion_detection as MD
import video_streaming as VS
import object_detection as OD
import motion_triggered_recording as MTR
import database as db
import helper_functions as HF


def save_to_database(db_path: Path, shared_dict: dict):
    if shared_dict["OD_db_permission"] and shared_dict["MTR_db_permission"]:
        if shared_dict['MTR_video_path_to_db'].exists() and shared_dict['MTR_video_path_to_db'].is_file():
            db.insert_video_path_with_metadata(db_path, shared_dict['MTR_video_path_to_db'], 
                                                shared_dict['OD_detected_obj_to_db'])
        shared_dict["OD_db_permission"] = shared_dict["MTR_db_permission"] = False
        shared_dict["OD_detected_obj_to_db"] = Counter()
        shared_dict["MTR_video_path_to_db"] = Path()


def send_email_whatsapp_notification(shared_dict):
    if shared_dict["permission_to_send_alert"]:
        msg = "Motion detected."
        if not isinstance(shared_dict["OD_det_obj_info_for_alert"], Counter):
            raise ValueError("Object info for alert is not a Counter object.")
        objs_counter = shared_dict["OD_det_obj_info_for_alert"]
        if not sum(objs_counter.values()) == 0:
            keys = list(objs_counter.keys())
            len_of_keys = len(keys)
            if len_of_keys == 1:
                msg+= f"\n{objs_counter[keys[0]]} {keys[0]} detected in the scene."
            else:
                for i in range(len_of_keys):
                    if i == 0:
                        msg+= f"\n{objs_counter[keys[i]]} {keys[i]}"
                    elif i == len_of_keys - 1:
                        msg+= f" and {objs_counter[keys[i]]} {keys[i]} detected in the scene."
                    else:
                        msg+= f", {objs_counter[keys[i]]} {keys[i]}"
        print(f"Sending notification: {msg}")
        shared_dict["permission_to_send_alert"] = False
        shared_dict["OD_det_obj_info_for_alert"] = Counter()
            

def video_stream(shm_name, frame_shape, shared_dict):
    print("live streaming started...")
    cam_track = VS.SharedVideoStreamTrack(shm_name, frame_shape, fps=30)
    asyncio.run(VS.listen(shared_dict, cam_track))



if __name__ == "__main__":
    db_path = Path(__file__).parent / "database" / "video_with_metadata.db"
    if db_path.exists():
        print("Database already exists.")
    else:
        db.create_db(db_path)
        print("Database created.")

    video_path = Path(__file__).parent / "gsoc.mp4"
    video_path = 0
    try:
        cap = HF.assign_cap_base_on_os(video_path)
    except Exception as e:
        print(f"Error: {e}")
        exit()
    
    if not cap or not cap.isOpened():
        raise RuntimeError("Failed to open video capture.")
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Error: Cannot read the video file.")

    frame_shape = frame.shape
    fps = cap.get(cv2.CAP_PROP_FPS)
    resolution = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print(f"FPS: {fps}")
    print(f"Camera width: {resolution[0]}")
    print(f"Camera height: {resolution[1]}")
    cap.release()
    time.sleep(20) # delay is necessary to free camera resources before starting capture_frames_main process

    shm_name = "cam_frame"

    size_in_bytes = int(np.prod(frame_shape) * np.dtype(np.uint8).itemsize)
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=size_in_bytes)

    event_dict = {"create_other_processes": Event(), "recording": Event()}
    barrier_dict = {"MD_OD": Barrier(2), "OD_MTR": Barrier(2)}

    with Manager() as manager:
        shared_dict = manager.dict()
        shared_dict["stop"] = False
        shared_dict["motion_detected"] = False
        shared_dict["recording"] = False
        shared_dict["permission_to_send_alert"] = False
        shared_dict["OD_det_obj_info_for_alert"] = Counter()

        shared_dict["OD_db_permission"] = False
        shared_dict["OD_detected_obj_to_db"] = Counter()

        shared_dict["MTR_db_permission"] = False
        shared_dict["MTR_video_path_to_db"] = Path()

        p1 = Process(target=CF.capture_frames_main, args=(video_path, shm_name, frame_shape, shared_dict, event_dict))
        p1.start()
        
        event_dict["create_other_processes"].wait() # Wait until the process p1 signals it's ready

        p2 = Process(target=MD.motion_detection_main, args=(shm_name, frame_shape, shared_dict, barrier_dict))
        p2.start()
        
        recording_length = 20
        p3 = Process(target=MTR.motion_triggered_recording_main, args=(shm_name, frame_shape, shared_dict, event_dict, barrier_dict, recording_length, resolution))
        p3.start()

        p4 = Process(target=OD.object_detection_main, args=(shm_name, frame_shape, shared_dict, event_dict, barrier_dict))
        p4.start()

        p5 = Process(target=video_stream, args=(shm_name, frame_shape, shared_dict,))
        p5.start()   

        while not shared_dict["stop"]:
            send_email_whatsapp_notification(shared_dict)
            save_to_database(db_path, shared_dict)


        p1.join()
        barrier_dict["MD_OD"].abort()
        barrier_dict["OD_MTR"].abort()
        p2.join()
        p3.join()
        p4.join() 
        time.sleep(3)
        p5.terminate()  # Forcefully kill p4
        cv2.destroyAllWindows()
        shm.close()
        shm.unlink()
        print("all processes finished")




