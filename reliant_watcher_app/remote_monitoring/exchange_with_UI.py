import asyncio  # Provides asynchronous I/O support
import json  # For encoding and decoding JSON messages
import database_manager as DBM  # Module for interacting with the database
import object_detection as OB  # Module for object detection (YOLOX in this case)


# Asynchronously sends the list of YOLOX objects over the provided channel.
# Constructs a JSON message with the action "send_yolox_objects" and a list of detected objects.
async def send_yolox_objects(channel):
    channel.send(json.dumps({
        "action": "send_yolox_objects",
        "yolox_objects": list(OB.YoloX._objects),  # Convert the set of objects to a list
    }))


# Asynchronously sends the latest intrusion videos and their metadata.
# It fetches the latest intrusion videos from the database using a thread executor to avoid blocking.
async def send_latest_intrusion_videos(channel, amount):
    # Run DBM.get_latest_intrusion_videos in a separate thread to keep the event loop responsive
    videos_with_metadata = await asyncio.get_event_loop().run_in_executor(
        None, DBM.get_latest_intrusion_videos, amount
    )
    # Send a JSON message with the retrieved videos and metadata
    channel.send(json.dumps({
        "action": "send_latest_intrusion_videos",
        "videos_with_metadata": videos_with_metadata,  # Dictionary mapping video_path to message
    }))


# Asynchronously processes a search for intrusion videos based on provided criteria.
# Validates that at least one criterion is given and, if valid, performs the search.
async def send_searched_intrusion_videos(channel, objects: list, start_date: str, end_date: str):
    # Server-side validation: ensure at least one search criterion is provided
    if (not objects or len(objects) == 0) and (not start_date or start_date.strip() == "") and \
       (not end_date or end_date.strip() == ""):
        # If validation fails, send an error message back over the channel
        channel.send(json.dumps({
            "action": "error",
            "error_message": "Please provide at least one search criterion: objects, start_date, or end_date."
        }))
        return

    # If validation passes, perform the search asynchronously using a thread executor
    videos_with_metadata = await asyncio.get_event_loop().run_in_executor(
        None, DBM.get_searched_intrusion_videos, objects, start_date, end_date
    )
    # Send the search results as a JSON message
    channel.send(json.dumps({
        "action": "send_searched_intrusion_videos",
        "videos_with_metadata": videos_with_metadata,  # Dictionary mapping video_path to message
    }))


# Asynchronously sends a file in chunks over the provided channel.
# Retrieves the file path, verifies its existence, then reads and sends the file in binary chunks.
async def send_file_in_chunks(channel, filename, video_player_id):
    # Retrieve the file path asynchronously using the database manager
    video_path = await asyncio.get_event_loop().run_in_executor(
        None, DBM.get_video_path, filename
    )
    # Check if the file exists and is indeed a file
    if not video_path.exists() or not video_path.is_file():
        error_msg = {
            "action": "download_error",
            "message": f"File '{filename}' not found on server."
        }
        channel.send(json.dumps(error_msg))
        return

    chunk_size = 64 * 1024  # Define the chunk size (64KB) for reading the file
    try:
        # Open the file in binary read mode
        with open(video_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)  # Read a chunk from the file
                if not chunk:
                    break  # Exit loop if end of file is reached
                # Send the binary chunk over the channel; the channel handles raw binary data
                channel.send(chunk)
        # Once all chunks have been sent, send a JSON message indicating download completion
        complete_msg = {
            "action": "download_complete",
            "filename": filename,
            "video_player_id": video_player_id
        }
        channel.send(json.dumps(complete_msg))
    except Exception as e:
        # In case an error occurs, send a download error message with the error details
        error_msg = {
            "action": "download_error",
            "message": str(e)
        }
        channel.send(json.dumps(error_msg))
