
import numpy as np
import cv2
from pathlib import Path
from collections import Counter
import math
from .yolox import YoloX  


def counter_greater_than_comparison(counter1, counter2):
    """
    Compare two Counter objects to determine if counter1 has any count greater than counter2.
    
    Parameters:
        counter1 (Counter): The first counter to compare.
        counter2 (Counter): The second counter to compare.
    
    Raises:
        TypeError: If either counter1 or counter2 is not an instance of Counter.
    
    Returns:
        bool: True if counter1 has a greater count for any key compared to counter2, otherwise False.
    """
    # Validate input types for counter1 and counter2
    if not isinstance(counter1, Counter) and not isinstance(counter2, Counter):
        raise TypeError("counter2 should be of type Counter.")
    
    # Iterate through all keys in the first counter
    for key in counter1.keys():
        # If key is not present in counter2 and count in counter1 is positive, return True
        if (key not in counter2) and counter1[key] > 0:
            return True
        # If the count for a key in counter1 is greater than in counter2, return True
        if counter1[key] > counter2[key]:
            return True
    return False


class ObjectDetection():
    """
    A class for performing object detection using the YOLOX model.
    
    This class handles preprocessing of frames, making predictions, aggregating results,
    visualizing detections, and computing background objects.
    """
    
    def __init__(self):
        # Define the target input size for the model
        self.target_size = (320, 320)
        # Initialize the YOLOX model with specified parameters
        self.model = YoloX(
            modelPath=Path(__file__).parent.joinpath("object_detection_yolox_2022nov.onnx"),
            input_size=self.target_size,
            confThreshold=0.3,
            nmsThreshold=0.3,
            objThreshold=0.3,
            backendId=cv2.dnn.DNN_BACKEND_OPENCV,
            targetId=cv2.dnn.DNN_TARGET_CPU
        )
        # Initialize various attributes to track detected objects and performance
        self.prev_objs = None           # Holds objects detected in the previous frame
        self.curr_objs = None           # Holds objects detected in the current frame
        self.cnt = 0                    # Frame counter
        self.aggregated_objects = Counter()  # Aggregated detection results over multiple frames
        self.background_objects = None  # Background objects computed over a time period
        self.max_fps_obtained = None    # Maximum frames per second recorded
        self.sensitivity = 1            # Sensitivity factor for updating detection results
        self.tm = cv2.TickMeter()       # Timer for measuring processing time
        self.tm.reset()
 
    def scale_frame_to_match_model_target_size(self, frame):
        """
        Resizes and pads the input frame to match the model's target input size.
        
        The function creates a padded frame with a constant value (114.0) and resizes the
        input frame while maintaining its aspect ratio.
        
        Parameters:
            frame (numpy.ndarray): The original frame to be processed.
            
        Returns:
            tuple: The padded and resized frame along with the scaling ratio.
        """
        # Create a padded frame with a constant value (114.0) for all pixels
        padded_frame = np.ones((self.target_size[0], self.target_size[1], 3), dtype=np.float32) * 114.0
        
        # Calculate the scaling ratio to maintain aspect ratio
        ratio = min(self.target_size[0] / frame.shape[0], self.target_size[1] / frame.shape[1])
        
        # Resize the frame using the computed ratio
        resized_img = cv2.resize(
            frame, 
            (int(frame.shape[1] * ratio), int(frame.shape[0] * ratio)), 
            interpolation=cv2.INTER_AREA
        ).astype(np.float32)
        
        # Insert the resized image into the top-left portion of the padded frame
        padded_frame[: int(frame.shape[0] * ratio), : int(frame.shape[1] * ratio)] = resized_img
        return padded_frame, ratio

    def prediction(self, frame):
        """
        Processes the frame, performs object detection, and computes FPS.
        
        This method converts the frame to RGB, scales it to the target size, and then
        performs inference using the YOLOX model. It also calculates the FPS based on
        the inference time.
        
        Parameters:
            frame (numpy.ndarray): The original frame to be analyzed.
            
        Returns:
            tuple: A tuple containing the predictions and the scaling factor used.
        """
        # Convert BGR to RGB format
        input = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Scale the frame to match the model's input size
        scaled_input, scale = self.scale_frame_to_match_model_target_size(input)
        # Start the timer before inference
        self.tm.start()
        # Run the model inference on the scaled input
        predictions = self.model.infer(scaled_input)
        # Stop the timer after inference
        self.tm.stop()
        # Calculate the frames per second (FPS)
        fps = math.ceil(self.tm.getFPS())
        self.max_fps_obtained = fps
        # Reset the timer for the next prediction
        self.tm.reset()
        return predictions, scale
    
    def predicted_objects_per_frame(self, predictions):
        """
        Count the number of detected objects per frame using a Counter.
        
        This method extracts the class IDs from each prediction and maps them to the
        corresponding object names defined in the model.
        
        Parameters:
            predictions (list): A list of predictions returned by the model.
            
        Returns:
            Counter: A Counter object with object names as keys and their occurrence as values.
        """
        detected_classes = Counter()
        for p in predictions:
            # Extract the class id from the prediction and convert it to an integer
            cls_id = int(p[-1])
            # Update the counter using the object's name from the model's objects mapping
            detected_classes.update([self.model.objects[cls_id]])
        return detected_classes
    
    def detecting_objects(self, frame, visualize=True):
        """
        Detect objects in the frame and update internal aggregated object counts.
        
        This method processes a frame to generate predictions, updates the current and previous
        detection counters, and aggregates objects based on certain time intervals. Optionally,
        it visualizes the detections.
        
        Parameters:
            frame (numpy.ndarray): The input frame for object detection.
            visualize (bool): Whether to display the detection visualization (default is True).
        """
        # Get predictions and scaling factor for the input frame
        predictions, scale = self.prediction(frame)
        # Update the current objects detected in this frame
        self.curr_objs = self.predicted_objects_per_frame(predictions)
        
        # For the first frame, simply initialize the previous objects counter
        if self.cnt == 0:
            self.prev_objs = self.curr_objs  
        # Every (max_fps_obtained * sensitivity) frames, aggregate objects using union/intersection logic
        elif self.cnt % (self.max_fps_obtained * self.sensitivity) == 0:
            # Aggregate using union of previous aggregated objects with intersection of prev and current
            self.aggregated_objects = self.aggregated_objects | (self.prev_objs & self.curr_objs)
            self.prev_objs = self.curr_objs
        else:
            # Update previous objects as the intersection of previous and current detections
            self.prev_objs = self.prev_objs & self.curr_objs
        
        # Increment the frame counter
        self.cnt += 1
        
        # Optionally visualize the detections on the frame
        if visualize:
            self.visualize(predictions, frame, scale)

    def visualize(self, predictions, frame, scale):
        """
        Visualize the detected objects on the frame by drawing bounding boxes and labels.
        
        This method overlays the detection results (bounding boxes, confidence scores, and labels)
        onto a copy of the input frame, displays the FPS, and then shows the resulting frame.
        
        Parameters:
            predictions (list): A list of predictions from the model.
            frame (numpy.ndarray): The original frame to annotate.
            scale (float): The scaling factor used to resize the frame.
        """
        # Create a copy of the original frame to draw annotations
        frame_clone = frame.copy()

        # Prepare and draw the FPS label on the frame
        fps_label = f"FPS: {self.max_fps_obtained}"
        cv2.putText(frame_clone, fps_label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Iterate over each prediction to draw bounding boxes and labels
        for p in predictions:
            # Extract and scale the bounding box coordinates back to the original frame size
            box = (p[:4] / scale).astype(np.int32)
            score = p[-2]       # Confidence score
            cls_id = int(p[-1]) # Class ID of the detected object
            x0, y0, x1, y1 = box
            # Prepare label text with object name and confidence percentage
            text = f"{self.model.objects[cls_id]} : {score*100}%"
            font = cv2.FONT_HERSHEY_SIMPLEX
            txt_size = cv2.getTextSize(text, font, 0.4, 1)[0]
            # Draw the bounding box for the detected object
            cv2.rectangle(frame_clone, (x0, y0), (x1, y1), (0, 255, 0), 2)
            # Draw a filled rectangle for the text background
            cv2.rectangle(frame_clone, (x0, y0 + 1), (x0 + txt_size[0] + 1, y0 + int(1.5 * txt_size[1])), (255, 255, 255), -1)
            # Overlay the label text on the frame
            cv2.putText(frame_clone, text, (x0, y0 + txt_size[1]), font, 0.4, (0, 0, 0), thickness=1)

        # Display the annotated frame in a window
        cv2.imshow("Object Detection Visualization", frame_clone)

    def set_1st_fps(self, frame):
        """
        A helper method to run a prediction on the first frame in order to establish FPS.
        
        Parameters:
            frame (numpy.ndarray): The initial frame used to compute FPS.
        """
        self.prediction(frame)

    def compute_background_objects(self, frame_obj, seconds=3, visualize=False):
        """
        Compute background objects over a period by aggregating object detections.
        
        This method runs the detection continuously for a specified number of seconds
        (which must be greater than the sensitivity setting) and aggregates detected objects
        to compute the background objects.
        
        Parameters:
            frame_obj (numpy.ndarray): The frame used repeatedly for background computation.
            seconds (int): The duration over which to compute background objects.
            visualize (bool): Whether to visualize detections during computation.
            
        Raises:
            ValueError: If the seconds parameter is not greater than sensitivity.
        """
        # Ensure the seconds parameter is larger than the sensitivity value
        if seconds <= self.sensitivity:
            raise ValueError("Seconds should be greater than sensitivity.")
        
        # Initialize FPS computation with the first frame
        self.set_1st_fps(frame_obj)
        
        # Run detections until the frame count reaches a multiple of (max_fps * seconds)
        while self.cnt == 0 or (self.cnt % (self.max_fps_obtained * seconds) != 0):
            self.detecting_objects(frame_obj, visualize)
        # After the loop, set the background objects based on aggregated detections
        self.background_objects = self.aggregated_objects

    def get_background_objects(self):
        """
        Retrieve the computed background objects.
        
        Returns:
            Counter: The background objects detected.
            
        Raises:
            ValueError: If the background objects have not been computed yet.
        """
        if self.background_objects is None:
            raise ValueError("Background objects not computed yet.")
        return self.background_objects
    
    def detected_objects_so_far(self):
        """
        Print and return the difference between aggregated objects and background objects.
        
        This represents the objects detected so far that are not part of the background.
        
        Returns:
            Counter: The difference between aggregated objects and background objects.
        """
        # Debug prints for aggregated vs background objects
        print(f"{self.aggregated_objects} - {self.background_objects}")
        print(f"{self.aggregated_objects - self.background_objects}")
        return self.aggregated_objects - self.background_objects

    def clear_aggregated_objects(self):
        """
        Reset the aggregated objects counter and frame counter.
        
        This is useful for restarting object detection without previous state interference.
        """
        self.aggregated_objects = Counter()
        self.cnt = 0
