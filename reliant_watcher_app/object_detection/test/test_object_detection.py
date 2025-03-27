import numpy as np
import cv2
import pytest
from collections import Counter

from pathlib import Path
import sys


# # Determine the parent directory
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

# # Add the parent directory to sys.path
sys.path.insert(0, str(PROJECT_DIR))

from object_detection.object_detection import ObjectDetection, counter_greater_than_comparison


# Define a dummy TickMeter that always returns 1 FPS.
class DummyTickMeter:
    def start(self):
        pass
    def stop(self):
        pass
    def reset(self):
        pass
    def getFPS(self):
        return 1.0

# Dummy inference function that always returns a single detection (e.g. "person").
def dummy_infer_constant(frame):
    # Each prediction is an array: [x0, y0, x1, y1, score, class_id]
    # Here, class_id 0 corresponds to "person".
    return [np.array([0, 0, 100, 100, 0.9, 0])]

# Dummy inference function that returns two detections: one "person" and one "car".
def dummy_infer_with_car(frame):
    # class_id 0 -> "person", class_id 1 -> "car"
    return [
        np.array([0, 0, 100, 100, 0.9, 0]),
        np.array([150, 150, 250, 250, 0.8, 1])
    ]

# Create a dummy frame (e.g. a black image)
def dummy_frame():
    return np.zeros((480, 640, 3), dtype=np.uint8)

# Fixture to create and configure an ObjectDetection instance for testing.
@pytest.fixture
def detection_instance(monkeypatch):
    od = ObjectDetection()
    # Override the model’s inference function.
    od.model.infer = dummy_infer_constant
    # Instead of patching the read-only property 'objects', override the underlying _objects attribute.
    od.model._objects = ('person', 'car')
    od.sensitivity = 1
    od.tm = DummyTickMeter()
    # Override cv2.imshow to avoid opening windows during tests.
    monkeypatch.setattr(cv2, 'imshow', lambda win, img: None)
    return od

def test_compute_background_objects(detection_instance):
    """
    Test that compute_background_objects correctly aggregates the background objects.
    Using dummy_infer_constant (always "person"), with seconds=3 and 1 FPS,
    the loop runs 3 times and the background should be Counter({'person': 1}).
    """
    frame = dummy_frame()
    detection_instance.compute_background_objects(frame, seconds=3, visualize=False)
    bg_objects = detection_instance.get_background_objects()
    expected_bg = Counter({'person': 1})
    assert bg_objects == expected_bg, f"Expected background objects {expected_bg}, got {bg_objects}"

def test_detected_objects_so_far(detection_instance):
    """
    After computing the background (with only "person"), simulate additional frames
    where an extra object ("car") appears. After two such frames, the aggregated objects
    should include both "person" and "car", and thus detected_objects_so_far (the difference)
    should return Counter({'car': 1}).
    """
    frame = dummy_frame()
    # Compute background with constant "person" detections.
    detection_instance.compute_background_objects(frame, seconds=3, visualize=False)
    # Now simulate new frames where both "person" and "car" are detected.
    detection_instance.model.infer = dummy_infer_with_car
    # Process two new frames.
    detection_instance.detecting_objects(frame, visualize=False)
    detection_instance.detecting_objects(frame, visualize=False)
    detected_diff = detection_instance.detected_objects_so_far()
    expected_diff = Counter({'car': 1})
    assert detected_diff == expected_diff, f"Expected detected objects so far {expected_diff}, got {detected_diff}"



def test_non_counter_both():
    """Test that if neither input is a Counter, a TypeError is raised."""
    with pytest.raises(TypeError):
        counter_greater_than_comparison("not a counter", "also not a counter")

def test_non_counter_first():
    """
    If only the first argument is not a Counter, then calling .keys() on it should
    raise an AttributeError.
    """
    with pytest.raises(AttributeError):
        counter_greater_than_comparison("not a counter", Counter({'a': 1}))

def test_empty_counters():
    """Test that comparing two empty counters returns False."""
    c1 = Counter()
    c2 = Counter()
    assert counter_greater_than_comparison(c1, c2) is False

def test_missing_key():
    """
    If counter1 has a key that is missing in counter2 with a positive count,
    the function should return True.
    """
    c1 = Counter({'a': 1})
    c2 = Counter()
    assert counter_greater_than_comparison(c1, c2) is True

def test_less_count():
    """
    If counter1 has the same key as counter2 but with a lower count,
    the function should return False.
    """
    c1 = Counter({'a': 1})
    c2 = Counter({'a': 2})
    assert counter_greater_than_comparison(c1, c2) is False

def test_greater_count():
    """
    If counter1 has a higher count than counter2 for a given key,
    the function should return True.
    """
    c1 = Counter({'a': 3})
    c2 = Counter({'a': 2})
    assert counter_greater_than_comparison(c1, c2) is True

def test_equal_counts():
    """
    If both counters have exactly the same counts for all keys,
    the function should return False.
    """
    c1 = Counter({'a': 1, 'b': 2})
    c2 = Counter({'a': 1, 'b': 2})
    assert counter_greater_than_comparison(c1, c2) is False

def test_multiple_keys():
    """
    When counter1 contains an additional key (or a higher count for an existing key)
    compared to counter2, the function should return True.
    """
    c1 = Counter({'a': 1, 'b': 2})
    c2 = Counter({'a': 1})
    assert counter_greater_than_comparison(c1, c2) is True
