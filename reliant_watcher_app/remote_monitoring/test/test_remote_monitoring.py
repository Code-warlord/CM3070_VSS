import asyncio  # For asynchronous I/O operations
from aiortc import VideoStreamTrack  # Base class for video streaming tracks in WebRTC
from fractions import Fraction  # To set the video frame's time base as a fraction
from pathlib import Path  # For cross-platform path manipulation
import sys  # To modify the Python path for module imports
import cv2  # OpenCV for capturing video from the camera
from av import VideoFrame  # For creating and handling video frames

# Determine the parent directory of the project by resolving the current file's path
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

# Insert the parent directory at the beginning of sys.path so that the remote_monitoring module can be imported
sys.path.insert(0, str(PROJECT_DIR))

import remote_monitoring as RM  # Import the remote monitoring module

# Define a custom VideoStreamTrack for testing using the webcam
class TestVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_index=0, fps=30):
        """
        Initialize the TestVideoStreamTrack.
        :param camera_index: The index of the camera to use (default is 0)
        :param fps: Target frames per second for video streaming
        """
        super().__init__()  # Initialize the base VideoStreamTrack
        self.camera_index = camera_index
        # Open a video capture object for the given camera index
        self.cap = cv2.VideoCapture(self.camera_index)
        self.fps = fps
        self.counter = 0  # Counter for assigning unique presentation timestamps (PTS)

    async def recv(self):
        """
        Asynchronously receive a video frame from the camera.
        This function maintains the target FPS by sleeping for an appropriate time,
        then reads a frame, converts it to a VideoFrame, and sets its PTS and time_base.
        """
        # Wait to maintain the target FPS
        await asyncio.sleep(1 / self.fps)

        # Capture a frame from the webcam
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read camera frame.")
        
        # Convert the captured frame (as an ndarray) to a VideoFrame with BGR color format
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")

        # Increment counter to be used as the frame's presentation timestamp (PTS)
        self.counter += 1
        video_frame.pts = self.counter
        # Set the frame's time base according to the target FPS
        video_frame.time_base = Fraction(1, self.fps)
        return video_frame
    
    def reset(self):
        """
        Reset the video capture by releasing and reinitializing it.
        This is useful if the camera needs to be restarted.
        """
        self.cap.release()  # Release the current video capture
        self.cap = cv2.VideoCapture(self.camera_index)  # Reopen the video capture
        self.counter = 0  # Reset the frame counter

    def stop(self):
        """
        Stop the video stream by releasing the video capture resource and calling the parent stop method.
        """
        self.cap.release()  # Release the camera resource
        super().stop()  # Call the parent class's stop method

# Main execution: If this script is run directly, start the remote monitoring listener.
if __name__ == "__main__":
    # Create a loop control dictionary; this can be used to signal the loop to stop
    loop = {"stop": False}
    # Run the remote monitoring listener asynchronously with the TestVideoStreamTrack instance
    asyncio.run(RM.listen(loop, TestVideoStreamTrack(camera_index=0, fps=30)))
