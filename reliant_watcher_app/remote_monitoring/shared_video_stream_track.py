import asyncio  # Provides asynchronous support for non-blocking operations
from aiortc import VideoStreamTrack  # Base class for custom video stream tracks in WebRTC
from fractions import Fraction  # For setting a fractional time base on video frames

from av import VideoFrame  # For creating video frames from NumPy arrays
from multiprocessing import shared_memory  # For inter-process shared memory handling
import numpy as np  # For numerical operations and array manipulations

# Custom VideoStreamTrack that reads video frames from a shared memory buffer.
class SharedVideoStreamTrack(VideoStreamTrack):
    def __init__(self, shm_name, frame_shape, fps=30):
        """
        Initialize the SharedVideoStreamTrack.

        Parameters:
        shm_name (str): The name of the shared memory block.
        frame_shape (tuple): The shape (height, width, channels) of the video frame.
        fps (int): The target frames per second.
        """
        super().__init__()  # Initialize the base VideoStreamTrack class.
        # Connect to an existing shared memory block by name (do not create a new one)
        self.shm = shared_memory.SharedMemory(name=shm_name, create=False)
        # Create a NumPy array that maps to the shared memory buffer using the provided frame shape.
        self.shared_frame = np.ndarray(frame_shape, dtype=np.uint8, buffer=self.shm.buf)
        self.fps = fps  # Store the target frames per second.
        self.counter = 0  # Initialize a counter to assign presentation timestamps (PTS).

    async def recv(self):
        """
        Asynchronously receive a video frame from the shared memory buffer.

        This method waits to maintain the target frame rate, converts the shared memory
        array to a VideoFrame, sets the presentation timestamp and time base, and then returns the frame.
        """
        # Sleep to maintain the target frame rate.
        await asyncio.sleep(1 / self.fps)
        
        # Create a VideoFrame from the shared memory NumPy array using BGR24 format.
        video_frame = VideoFrame.from_ndarray(self.shared_frame, format="bgr24")

        # Increment the counter to use as the frame's presentation timestamp (PTS).
        self.counter += 1
        video_frame.pts = self.counter
        # Set the time base, which defines the duration per frame.
        video_frame.time_base = Fraction(1, self.fps)
        return video_frame  # Return the prepared video frame.
    
    def reset(self):
        """
        Reset the video stream track.

        Closes and reopens the shared memory connection, reinitializes the NumPy array,
        and resets the frame counter.
        """
        self.shm.close()  # Close the current shared memory connection.
        # Reopen the shared memory with the same name to refresh the connection.
        self.shm = shared_memory.SharedMemory(name=self.shm.name, create=False)
        # Recreate the NumPy array mapping to the shared memory buffer using the original shape.
        self.shared_frame = np.ndarray(self.shared_frame.shape, dtype=np.uint8, buffer=self.shm.buf)
        self.counter = 0  # Reset the frame counter.

    def stop(self):
        """
        Stop the video stream track.

        Closes the shared memory resource and calls the parent stop method to finalize shutdown.
        """
        self.shm.close()  # Close the shared memory connection to free resources.
        super().stop()  # Call the parent class's stop method.
