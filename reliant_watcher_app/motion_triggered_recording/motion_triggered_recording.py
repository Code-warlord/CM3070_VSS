import numpy as np 
from multiprocessing import shared_memory 
import time
from datetime import datetime
import subprocess 
from pathlib import Path 


def ffmpeg_parameters(resolution: tuple, file_path: Path, target_fps: float):
    """
    Construct the FFmpeg command parameters for video recording.

    Parameters:
        resolution (tuple): Desired video resolution (width, height).
        file_path (Path): The path where the output video will be saved.
        target_fps (float): The frame rate of the output video.

    Returns:
        list: A list of FFmpeg command line arguments.
    """
    return [
        "ffmpeg",
        "-loglevel", "error",         # Suppress all log messages except errors
        "-f", "rawvideo",              # Specify raw video format input
        "-vcodec", "rawvideo",         # Use raw video codec for input
        "-pix_fmt", "bgr24",           # Pixel format used by OpenCV (BGR format)
        "-s", f"{resolution[0]}x{resolution[1]}",  # Set video resolution (width x height)
        "-r", str(target_fps),         # Set the output frame rate
        "-i", "-",                   # Read input from standard input (pipe)
        "-c:v", "libx264",             # Use H.264 codec for video compression
        "-preset", "slow",             # Use a slower preset for a better quality/speed trade-off
        "-crf", "23",                  # Set the Constant Rate Factor (lower means better quality)
        "-y", file_path,               # Overwrite the output file if it exists
    ]
    

def motion_triggered_recording_main(shm_name: str, frame_shape: tuple, shared_dict: dict, event_dict: dict, 
                                      barrier_dict: dict, recording_length: int, resolution: tuple):
    """
    Main function for motion-triggered video recording.

    This function reads frames from a shared memory buffer, waits for a motion detection
    signal, and when motion is detected, it records a video segment using FFmpeg.
    
    Parameters:
        shm_name (str): Name of the shared memory block containing video frames.
        frame_shape (tuple): Shape (dimensions) of the video frame.
        shared_dict (dict): Dictionary for shared flags and data across processes.
        event_dict (dict): Dictionary for events used to synchronize processes.
        barrier_dict (dict): Dictionary for Barrier objects used for process synchronization.
        recording_length (int): Duration (in seconds) of the recording.
        resolution (tuple): Resolution (width, height) for the output video.
    """
    # Access the existing shared memory block by its name.
    shm = shared_memory.SharedMemory(name=shm_name, create=False)
    # Create a NumPy array that maps to the shared memory buffer to get the current video frame.
    shared_frame = np.ndarray(frame_shape, dtype=np.uint8, buffer=shm.buf)
    
    # Loop continuously until a stop flag is set in the shared dictionary.
    while not shared_dict["stop"]:
        # Check if motion has been detected to trigger recording.
        if shared_dict["motion_detected"]:
            # Wait at the "OD_MTR" barrier to synchronize with the object detection process.
            barrier_dict["OD_MTR"].wait()
            
            # Generate a timestamp to be used in the file name.
            shared_dict["time_stamp"] = datetime.now()
            # Create a file name based on the current timestamp (format: YYYY-MM-DD_HH-MM-SS.mp4)
            file_name = f"{shared_dict['time_stamp'].strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
            # Construct the file path where the video will be saved.
            file_path = Path(__file__).parent.parent / "video_recordings" / file_name
            # Define the target frame rate for recording.
            target_fps = 20.0

            # Build the FFmpeg command using the defined parameters.
            ffmpeg_cmd = ffmpeg_parameters(resolution, file_path, target_fps)

            # Start the FFmpeg process, with its standard input piped so that frames can be sent.
            ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

            # Initialize recording variables.
            frames_recorded = 0
            total_frames_expected = int(target_fps * recording_length)
            
            # Record frames until the expected number of frames is reached or a stop signal is given.
            while frames_recorded < total_frames_expected and not shared_dict["stop"]:
                # Set flags to indicate that recording is in progress.
                shared_dict["recording"] = True
                event_dict["recording"].set()
                start_time = time.time()
                # Write the current frame from shared memory to FFmpeg for encoding.
                ffmpeg_process.stdin.write(shared_frame.tobytes())
                frames_recorded += 1

                # Calculate delay to maintain a consistent frame rate.
                frame_delay = 1 / target_fps  # Expected delay between frames in seconds
                elapsed_time = time.time() - start_time
                if elapsed_time < frame_delay:
                    time.sleep(frame_delay - elapsed_time)

            # After recording, clear the recording event and reset the recording flag.
            event_dict["recording"].clear()
            shared_dict["recording"] = False
            print("recording ended.")
            
            # Close the FFmpeg process's input and wait for the process to complete.
            ffmpeg_process.stdin.close()
            ffmpeg_process.wait()
            # Set permission flags and share the recorded video's file name for database logging.
            shared_dict["MTR_db_permission"] = True
            shared_dict["MTR_video_name_to_db"] = file_name
            # Optionally, you could also share the full path:
            # shared_dict["MTR_video_path_to_db"] = file_path
            print("20 sec Recording completed.")
    
    # Once the loop ends, release resources and close the shared memory connection.
    print("Recording process exited.")
    shm.close()
