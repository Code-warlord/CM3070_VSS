import cv2
import platform



def assign_cap_base_on_os(recorded_video=None):
    try:
        # If a recorded video path is provided, use it.
        if recorded_video:
            cap = cv2.VideoCapture(recorded_video)
            if not cap.isOpened():
                raise RuntimeError(f"Unable to open recorded video file: {recorded_video}")
            return cap

        # No recorded video provided; open live capture based on OS.
        current_os = platform.system()
        if current_os == "Windows":
            cap = cv2.VideoCapture(0)
        elif current_os == "Linux":
            gst_pipeline = (
                "libcamerasrc ! "
                "video/x-raw,format=NV12,width=640,height=480,framerate=30/1 ! "
                "videoconvert ! "
                "appsink"
            )
            cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        else:
            raise NotImplementedError(f"OS '{current_os}' is not supported.")

        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video capture on {current_os}.")

        return cap

    except Exception as e:
        raise RuntimeError("Error in assign_cap_base_on_os: " + str(e))



def dimension_with_aspect_ratio(frame, size = None):
    (h, w) = frame.shape[:2]

    if h <= 0:
        raise ValueError ("Image height cannot be <= zero")
    elif w <= 0:
        raise ValueError ("Image weight cannot be <= zero")
    if size is None:
        new_dimensions = (w, h)
        scale_factor = 1.0  # No resizing needed
        return (new_dimensions, scale_factor)  # No resizing needed    

    if size < 100:
        raise ValueError ("Size can either be set to None or >= 100")
    
    if w > h:
        scale_factor = size / w
        new_dimensions = (size, int(h * scale_factor))
    else:
        scale_factor = size / h
        new_dimensions = (int(w * (scale_factor)), size)
    return (new_dimensions, scale_factor)

