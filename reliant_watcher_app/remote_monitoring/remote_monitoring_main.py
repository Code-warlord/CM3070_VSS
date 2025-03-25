
import asyncio
from .shared_video_stream_track import SharedVideoStreamTrack
from remote_monitoring import listen

def remote_monitoring_main(shm_name, frame_shape, shared_dict):
    print("live streaming started...")
    cam_track = SharedVideoStreamTrack(shm_name, frame_shape, fps=30)
    asyncio.run(listen(shared_dict, cam_track))