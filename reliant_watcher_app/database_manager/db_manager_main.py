
from pathlib import Path
from collections import Counter
import remote_monitoring as RM
from .db_manager import insert_video_with_metadata




def save_to_database(db_path: Path, shared_dict: dict):
    if shared_dict["OD_db_permission"] and shared_dict["MTR_db_permission"]:
        video_path = Path(__file__).parent.parent / "video_recordings" / shared_dict['MTR_video_name_to_db']
        if video_path.exists() and video_path.is_file():
            insert_video_with_metadata(db_path, shared_dict['MTR_video_name_to_db'], 
                                                shared_dict['OD_detected_obj_to_db'])
        shared_dict["OD_db_permission"] = shared_dict["MTR_db_permission"] = False
        shared_dict["OD_detected_obj_to_db"] = Counter()
        shared_dict["MTR_video_name_to_db"] = ""