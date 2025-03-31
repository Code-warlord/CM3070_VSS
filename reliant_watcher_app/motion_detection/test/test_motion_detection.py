import pytest
import numpy as np
import cv2
from pathlib import Path
import sys
import math

# # Determine the parent directory
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

# # Add the parent directory to sys.path
sys.path.insert(0, str(PROJECT_DIR))

from motion_detection.motion_detector import MotionDetector  # or wherever the class is defined


@pytest.fixture
def motion_detector():
    """
    Returns a fresh instance of MotionDetection for each test.
    """
    return MotionDetector()

@pytest.fixture
def video_capture():
    """
    Returns a function that creates a cv2.VideoCapture object for a given video path.
    If no path is provided, defaults to "gsoc.mp4" in the same directory as the test.
    """
    def get_capture(video_path=None):
        # Use default video if none is provided.
        if video_path is None:
            video_path = Path(__file__).parent.parent.parent / "test_videos" / "test_video_1_day.mp4"
        else:
            video_path = Path(video_path)
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video capture for {video_path}")
        
        # Read first frame to verify the video can be read.
        ret = cap.read()[0]
        if not ret:
            cap.release()
            raise RuntimeError(f"Cannot read the video file: {video_path}")
        return cap
    return get_capture

def test_set_min_detectable_area_before_dimension(motion_detector, video_capture):
    cap = video_capture()
    # Part 1: Without calling setup(), initialize_model() should raise a RuntimeError.
    with pytest.raises(RuntimeError) as err_msg:
        motion_detector.set_min_detectable_area()
    assert "Error: Call `set_dimension_and_scale_factor()` before `set_min_detectable_area()`." in str(err_msg.value), \
        "set_min_detectable_area() should raise a RuntimeError before set_dimension_and_scale_factor() is called."
    try:
        frame = cap.read()[1]
        motion_detector.set_dimension_and_scale_factor(frame)
        motion_detector.set_min_detectable_area()
    except Exception as e:
        pytest.fail(f"set_min_detectable_area() raised an exception unexpectedly: {e}")
    cap.release()

def test_initialize_before_setup_raises_err(motion_detector, video_capture):
    cap = video_capture()
    with pytest.raises(RuntimeError) as err_msg:
        motion_detector.initialize_model(cap.read()[1])
    assert "Error: Call `setup()` before `initialize_model()`." in str(err_msg.value), \
        "initialize_model() should raise a RuntimeError if called before setup()."
    motion_detector.setup(cap.read()[1], size=350)
    try:
        motion_detector.initialize_model(cap.read()[1])
    except Exception as e:
        pytest.fail(f"initialize_model() raised an exception unexpectedly: {e}")
    assert motion_detector.model_initialized is True, \
        "model_initialized should be True after initialize_model()"
    cap.release()

def test_motion_det_with_thres_before_init_model_raises_err(motion_detector, video_capture):
    cap = video_capture()
    with pytest.raises(RuntimeError) as err_msg:
        motion_detector.detect_motion_with_threshold(cap.read()[1])
    assert "Error: Call `initialize_model()` before `motion_detection_with_threshold()`." in str(err_msg.value), \
        "motion_detection_with_threshold() should raise a RuntimeError if called before initialize_model()."
    motion_detector.setup(cap.read()[1])
    motion_detector.initialize_model(cap.read()[1])
    try:
        motion_detector.detect_motion_with_threshold(cap.read()[1])
    except Exception as e:
        pytest.fail(f"motion_detection_with_threshold() raised an exception unexpectedly: {e}")
    cap.release()

# # -----------------------------------------------------------------------------
# # TESTS FOR CLASS METHODS (low-level checks)
# # -----------------------------------------------------------------------------
@pytest.mark.parametrize("motion_detector, blank_frame, size, expected_dimension", [
    (MotionDetector(), np.zeros((480, 640, 3), dtype=np.uint8), 350, (350, 262)),
    (MotionDetector(), np.zeros((480, 640, 3), dtype=np.uint8), 640, (640, 480)),
    (MotionDetector(), np.zeros((480, 640, 3), dtype=np.uint8), 640*2, (640*2, 480*2)),
])
def test_set_dimension_and_scale_factor(motion_detector, blank_frame, size, expected_dimension):
    """
    Test that set_dimension_and_scale_factor correctly sets 
    dimension and scale_factor and does not raise an error for valid input.
    """
    motion_detector.set_dimension_and_scale_factor(blank_frame, size)
    assert motion_detector.dimension == expected_dimension, \
            f"Expected dimension to be {expected_dimension}, but got {motion_detector.dimension}"
    frame_width = blank_frame.shape[1]
    assert math.isclose(motion_detector.scale_factor, size/frame_width), \
            f"Expected scale_factor to be {size/frame_width}, but got {motion_detector.scale_factor}"

@pytest.mark.parametrize("motion_detector, blank_frame, size, expected_dimension", [
    (MotionDetector(), np.zeros((480, 640, 3), dtype=np.uint8), 80, (80, 60)),
])
def test_set_dimension_below_size_100_raise_err(motion_detector, blank_frame, size, expected_dimension):
    """
    Test that set_dimension_and_scale_factor correctly sets 
    dimension and scale_factor and does not raise an error for valid input.
    """
    try:
        motion_detector.set_dimension_and_scale_factor(blank_frame, size)
    except ValueError as v:
        assert "Size can either be set to None or >= 100" in str(v)


@pytest.mark.parametrize("motion_detector, blank_frame, size", [
    (MotionDetector(), np.zeros((480, 640, 3), dtype=np.uint8), 320),
    (MotionDetector(), np.zeros((480, 640, 3), dtype=np.uint8), 640),
    (MotionDetector(), np.zeros((480, 640, 3), dtype=np.uint8), 1000),
])
def test_set_min_detectable_area(motion_detector, blank_frame, size):
    """
    Test that set_min_detectable_area calculates and sets the attribute correctly
    after set_dimension_and_scale_factor is called.
    """
    # Must call set_dimension... first
    motion_detector.set_dimension_and_scale_factor(blank_frame, size)
    motion_detector.set_min_detectable_area()
    dimension_area = motion_detector.dimension[0] * motion_detector.dimension[1]
    assert motion_detector.min_detectable_area == pytest.approx(dimension_area / 1000), \
           f"Expected {dimension_area / 1000} but got {motion_detector.min_detectable_area}"

# -----------------------------------------------------------------------------
# TESTS FOR detect_motion()
# -----------------------------------------------------------------------------

# Parametrize the test with:
# - video_path: a Path to the test video,
# - ground_truth: a dict mapping expected start times (in seconds) to durations (in seconds),
# - size: desired width (e.g., 350)
@pytest.mark.parametrize("video_path, ground_truth, size", [
    (
        Path(__file__).parent.parent.parent / "test_videos" / "test_video_1_day.mp4", 
        {
            3.4: 0.96, 
            4.7: 0.83, 
            6.93: 6.9, 
            15.63: 0.93,
        },
        350,
    ),
    (
        Path(__file__).parent.parent.parent / "test_videos" / "test_video_2_night.mp4", 
        {
            2.3 : 9.73,
        },
        350,
    ),
])
def test_detect_motion_ok(motion_detector, video_capture, video_path, ground_truth, size):
    """
    Test that after initializing the motion detection model, the 
    motion_detector.detect_motion() method returns detection events that
    match the expected ground truth. The test reads frames from a video,
    captures detection events (with start time and duration), and verifies them.
    """
    # Open the video capture using the provided factory fixture.
    cap = video_capture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Use the first frame for setup.
    ret, frame = cap.read()
    if not ret:
        cap.release()
        pytest.fail("Failed to read the first frame for setup()")
    motion_detector.setup(frame, size)
    
    # Use a subsequent frame to initialize the model.
    ret, frame = cap.read()
    if not ret:
        cap.release()
        pytest.fail("Failed to read a frame for initialize_model()")
    motion_detector.initialize_model(frame)
    
    # Variables to capture detection events.
    step = 0
    observed_result = {}  # maps start_time (sec) to (duration (sec), contour)
    start_frame_cnt = None
    end_frame_cnt = None
    fg_mask = None
    observed_contour = None

    # Process remaining video frames.
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break 
        motion_detected, contour, fg_mask = motion_detector.detect_motion(frame)
        if motion_detected and step == 0:
            start_frame_cnt = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            observed_contour = contour
            step = 1
        elif not motion_detected and step == 1:
            end_frame_cnt = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            step = 2
        if step == 2:
            start_time = round(start_frame_cnt / fps, 2)
            duration = round((end_frame_cnt - start_frame_cnt) / fps, 2)
            observed_result[start_time] = (duration, observed_contour)
            # observed_result[start_time] = duration
            step = 0

        if step == 1: # this means that there was detected motion until the end of the video
            start_time = round(start_frame_cnt / fps, 2)
            duration = round((int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - start_frame_cnt) / fps, 2)
            observed_result[start_time] = (duration, observed_contour)

    cap.release()

    # Compare detections: sort ground truth and observed events by start time, then use zip.
    sorted_ground = sorted(ground_truth.items())
    sorted_observed = sorted(observed_result.items())
    assert len(sorted_ground) == len(sorted_observed), \
        f"Expected {len(sorted_ground)} detections, got {len(sorted_observed)}."

    for ((gt_start, gt_duration), (obs_start, (obs_duration, obs_contour))) in zip(sorted_ground, sorted_observed):
        assert math.isclose(gt_start, obs_start, abs_tol=1), \
            f"Expected start_time {gt_start}, got {obs_start}"
        assert math.isclose(gt_duration, obs_duration, abs_tol=1), \
            f"Expected duration {gt_duration}, got {obs_duration}"
        area = cv2.contourArea(obs_contour)
        assert area >= motion_detector.min_detectable_area, \
            f"Contour area {area} is below threshold {motion_detector.min_detectable_area}"

    # Final check: verify that fg_mask is valid and has the expected dimensions.
    expected_shape = (int(height * motion_detector.scale_factor), size)
    assert fg_mask is not None, "fg_mask is None"
    assert fg_mask.shape == expected_shape, f"Expected fg_mask shape {expected_shape}, got {fg_mask.shape}"


# Parametrize the test with:
# - video_path: a Path object for the test video,
# - ground_truth: a dictionary mapping expected detection start times (in seconds) to durations (in seconds),
# - size: desired resized width (e.g., 350).
@pytest.mark.parametrize("video_path, ground_truth, size", [
    (
        Path(__file__).parent.parent.parent / "test_videos" / "test_video_1_day.mp4", 
        {
            3.4: 0.96, 
            4.7: 0.83, 
            6.93: 6.9, 
            15.63: 0.93,
        },
        350,
    ),
    (
        Path(__file__).parent.parent.parent / "test_videos" / "test_video_2_night.mp4", 
        {
            2.3 : 9.73, 
        },
        350,
    ),
])
def test_detect_motion_with_threshold_ok(motion_detector, video_capture, video_path, ground_truth, size):
    """
    Test that after initializing the motion detection model, the 
    motion_detector.detect_motion_with_threshold() method returns detection events 
    matching the expected ground truth. The test processes frames from a video, 
    records when motion is detected (as a start time) and its duration, and compares 
    these values with the expected values.
    """
    # Open the video capture using the factory fixture.
    cap = video_capture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Read the first frame and use it for setup().
    ret, frame = cap.read()
    if not ret:
        cap.release()
        pytest.fail("Failed to read the first frame for setup()")
    motion_detector.setup(frame, size)
    
    # Read another frame to initialize the model.
    ret, frame = cap.read()
    if not ret:
        cap.release()
        pytest.fail("Failed to read a frame for initialize_model()")
    motion_detector.initialize_model(frame)
    
    # Variables to capture detection events.
    step = 0
    observed_result = {}  # Maps start_time (sec) -> duration (sec)
    start_frame_cnt = None
    end_frame_cnt = None
    motion_detected_threshold=2
    # Process the remaining frames.
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break 
        # detect_motion_with_threshold returns a boolean.
        motion_detected = motion_detector.detect_motion_with_threshold(frame, motion_detected_threshold)
        if motion_detected and step == 0:
            start_frame_cnt = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            step = 1
        elif not motion_detected and step == 1:
            end_frame_cnt = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            step = 2
        if step == 2:
            start_time = round(start_frame_cnt / fps, 2)
            duration = round((end_frame_cnt - start_frame_cnt) / fps, 2)
            observed_result[start_time] = duration
            step = 0

    cap.release()

    # Filter ground truth to consider only detections with duration >= motion_detector.motion_detected_threshold.
    filtered_ground_truth = {k: v for k, v in ground_truth.items() 
                             if v >= motion_detected_threshold}

    # Compare number of detections.
    assert len(filtered_ground_truth) == len(observed_result), \
        f"Expected {len(filtered_ground_truth)} detections with duration >= {motion_detected_threshold} secs, \
        got {len(observed_result)}."
    
    # Compare the detections in sorted order using zip.
    for ((gt_start, gt_duration), (obs_start, obs_duration)) in zip(
            sorted(filtered_ground_truth.items()), sorted(observed_result.items())):
        # In this example, we assume that the observed start time should be shifted by the threshold.
        expected_obs_start = gt_start + motion_detected_threshold
        expected_obs_duration = gt_duration - motion_detected_threshold
        assert math.isclose(expected_obs_start, obs_start, abs_tol=1), \
            f"Expected detection start time {expected_obs_start}, got {obs_start}"
        assert math.isclose(expected_obs_duration, obs_duration, abs_tol=1), \
            f"Expected detection duration {expected_obs_duration}, got {obs_duration}"

