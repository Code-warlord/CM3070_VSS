import cv2
import numpy as np
from pysubsense import BackgroundSubtractorSuBSENSE
import math
from pathlib import Path
import sys

# Determine the parent directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
# Add the parent directory to sys.path
sys.path.insert(0, str(PROJECT_DIR))

import helper_functions as HF



class MotionDetector:
    def __init__(self):
        self.subtractor = BackgroundSubtractorSuBSENSE()
        self.fps = 0.0
        self.consecutive_frames_with_motion = 0
        self.tm = cv2.TickMeter()
        self.tm.reset()
        self.dimension = None
        self.scale_factor = None
        self.model_initialized = False  # Flag to track if initialize_model() was called
        self.min_detectable_area = None
        # self.motion_detected_threshold = 1.5

    def set_dimension_and_scale_factor(self, frame, size=None):
        """Sets the resizing dimension and scale factor. Must be called before other functions."""
        try:
            self.dimension, self.scale_factor = HF.dimension_with_aspect_ratio(frame, size)
        except Exception as e:
            raise ValueError(f"{e}")
        
    def set_min_detectable_area(self):
        if self.dimension is None:
            raise RuntimeError("Error: Call `set_dimension_and_scale_factor()` before `set_min_detectable_area()`.")
        self.min_detectable_area = (self.dimension[0] * self.dimension[1]) / 1000

    def setup(self, frame, size=None):
        self.set_dimension_and_scale_factor(frame, size)
        self.set_min_detectable_area()


    def initialize_model(self, frame):
        """Initializes the motion detection model. Must be called after setting resize dimensions."""
        if self.dimension is None or self.scale_factor is None:
            raise RuntimeError("Error: Call `setup()` before `initialize_model()`.")

        try:
            resized_frame = cv2.resize(frame, self.dimension, interpolation=cv2.INTER_AREA)
            gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
            roi_frame = np.full_like(gray_frame, 255)
            self.subtractor.initialize(gray_frame, roi_frame)
            self.model_initialized = True  # Mark as initialized
        except Exception as e:
            raise RuntimeError(f"Error during model initialization: {e}")

    def detect_motion(self, frame):
        """Detects motion in a given frame and returns the contour if motion is found."""
        if not self.model_initialized:
            raise RuntimeError("Error: Call `initialize_model()` before `detect_motion()`.")

        try:
            resized_frame = cv2.resize(frame, self.dimension, interpolation=cv2.INTER_AREA)
            gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
            fg_mask = self.subtractor.apply(gray_frame)
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion_detected = False
            contour = None 
            for c in contours:
                if cv2.contourArea(c) >= self.min_detectable_area:
                    contour = (c / self.scale_factor).astype(np.int32)
                    motion_detected = True
                    break # one contour detected is enough to break the loop to gain computational speed
            return motion_detected, contour, fg_mask
        except Exception as e:
            raise RuntimeError(f"Error in motion detection: {e}")

    def detect_motion_with_threshold(self, frame:np.ndarray, motion_detected_threshold:float=2.0, visualize=False)->bool:
        """Performs motion detection and confirms motion if it persists beyond a threshold."""
        if not self.model_initialized:
            raise RuntimeError("Error: Call `initialize_model()` before `motion_detection_with_threshold()`.")
        try:
            self.tm.start()
            motion_detected, contour, fg_mask = self.detect_motion(frame)
            self.tm.stop()
            self.fps = self.tm.getFPS()

            if motion_detected:
                self.consecutive_frames_with_motion += 1
            else:
                self.consecutive_frames_with_motion = 0

            motion_confirmed = self.consecutive_frames_with_motion >= math.ceil(motion_detected_threshold * self.fps)

            if visualize:
                frame_ = frame.copy()
                cv2.drawContours(frame_, [contour], -1, (255, 255, 255), 2)
                text = "Motion Detected" if motion_confirmed else "Motion Not Detected"
                fps_text = f"FPS: {self.fps:.2f}"
                cv2.putText(frame_, text, (0, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_, fps_text, (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.imshow("Original Frame", frame_)
                cv2.imshow("Foreground Frame", fg_mask)

            return motion_confirmed
        except Exception as e:
            raise RuntimeError(f"Error in motion detection with threshold: {e}")
        
