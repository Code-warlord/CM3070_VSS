
import cv2
import numpy as np
from multiprocessing import shared_memory, Barrier
import time
from collections import Counter
from object_detection import ObjectDetection, counter_greater_than_comparison


def object_detection_main(shm_name: str, frame_shape: tuple, shared_dict: dict, event_dict: dict, barrier_dict: dict):
    """
    Main function for object detection that uses shared memory for accessing video frames,
    inter-process events for synchronization, and shared dictionaries for communication
    with other processes.

    Parameters:
        shm_name (str): Name of the shared memory block.
        frame_shape (tuple): The shape (dimensions) of the video frame.
        shared_dict (dict): Dictionary for shared flags and data across processes.
        event_dict (dict): Dictionary for shared events to synchronize actions.
        barrier_dict (dict): Dictionary for Barrier objects to synchronize multiple processes.
    """
    try:
        # Connect to the existing shared memory block using the provided name.
        shm = shared_memory.SharedMemory(name=shm_name, create=False)
        # Create a NumPy array that maps to the shared memory buffer with the specified frame shape.
        shared_frame = np.ndarray(frame_shape, dtype=np.uint8, buffer=shm.buf)
        
        # Initialize the object detection model.
        object_detection = ObjectDetection()
        # Compute background objects using the current shared frame without visualization.
        object_detection.compute_background_objects(shared_frame, visualize=False)
        
        # Wait until the "MD_OD" barrier is released (synchronization point with motion detection process).
        barrier_dict["MD_OD"].wait()
        
        # Initialize the variable to store the last set of detected objects.
        last_objects_detected = None
        
        # Main loop that runs until the shared "stop" flag is set.
        while not shared_dict["stop"]:
            # Reset last_objects_detected if no motion is detected.
            if not shared_dict["motion_detected"]:
                last_objects_detected = None

            # Wait at the "OD_MTR" barrier for synchronization with Motion Triggered Recording processes.
            barrier_dict["OD_MTR"].wait()
            
            # Initialize flags to ensure specific actions are executed only once during recording.
            executed1 = False
            executed2 = False
            # Preset times for sending alert and saving to database (in seconds).
            send_alert_msg_preset_time = 4
            save_to_database_preset_time = 19
            
            # Clear previous aggregated detection results before starting a new recording cycle.
            object_detection.clear_aggregated_objects()
            
            # Wait until the "recording" event is set.
            event_dict["recording"].wait()
            # Record the start time for the current recording cycle.
            start_time = time.time()
            
            # Inner loop runs while the "recording" flag in the shared dictionary is True.
            while shared_dict["recording"]:
                # Perform object detection on the current shared frame and visualize the results.
                object_detection.detecting_objects(shared_frame, visualize=True)
                
                # Check if the preset time for sending an alert message has been reached and hasn't been executed.
                if time.time() - start_time > send_alert_msg_preset_time and not executed1:
                    # If this is the first alert cycle, get the detected objects.
                    if last_objects_detected is None:
                        detected_objects = object_detection.detected_objects_so_far()
                        # Set flag in shared dictionary to allow sending an alert.
                        shared_dict["permission_to_send_alert"] = True
                        # Share the detected object information for the alert.
                        shared_dict["OD_det_obj_info_for_alert"] = detected_objects
                        # Update last_objects_detected with current detections.
                        last_objects_detected = detected_objects
                        executed1 = True
                    # For subsequent cycles, compare the current detections with the previous ones.
                    elif isinstance(last_objects_detected, Counter):
                        # If current detections exceed the last ones, update and send alert.
                        if counter_greater_than_comparison(detected_objects, last_objects_detected):
                            detected_objects = object_detection.detected_objects_so_far()
                            shared_dict["permission_to_send_alert"] = True
                            shared_dict["OD_det_obj_info_for_alert"] = detected_objects
                            # Merge current detections with previous ones.
                            last_objects_detected = last_objects_detected | detected_objects
                            executed1 = True

                # Check if the preset time for saving to the database has been reached and hasn't been executed.
                if time.time() - start_time > save_to_database_preset_time and not executed2:
                    detected_objects = object_detection.detected_objects_so_far()
                    # Set flag in shared dictionary to allow database saving.
                    shared_dict["OD_db_permission"] = True
                    # Share the detected object information for the database.
                    shared_dict["OD_detected_obj_to_db"] = detected_objects
                    executed2 = True
                    
                # Check if the 'q' key has been pressed to break the recording loop.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    shared_dict["stop"] = True
                    break
        
        # After exiting the main loop, close the shared memory connection.
        shm.close()
        exit()
    except FileNotFoundError:
        # Handle the error if the shared memory block does not exist.
        print(f"Shared memory '{shm_name}' does not exist.")
        shared_dict["stop"] = True
        exit()
