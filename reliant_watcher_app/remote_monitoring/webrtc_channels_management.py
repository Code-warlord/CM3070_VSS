import asyncio  # Provides support for asynchronous operations
import json  # For encoding and decoding JSON messages
from pathlib import Path  # For manipulating filesystem paths
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer  # WebRTC classes for peer connection setup
from .exchange_with_UI import send_latest_intrusion_videos, send_file_in_chunks, \
                                send_searched_intrusion_videos, send_yolox_objects  # Functions to exchange data with the UI

# Global variable to hold the current RTCPeerConnection instance
vss_pc = None

# Define the path to the authentication file for STUN and TURN server credentials
auth_file = Path(__file__).parent.parent / "auth" / "stun_and_turn_server_auth.json"

# Open and load the authentication details from the JSON file
with open(auth_file, "r") as file:
    auth_details = json.load(file)

# Create the ICE server configuration using the authentication details and public STUN/TURN servers
ice_config = RTCConfiguration(
    iceServers=[
        RTCIceServer(
            urls=["stun:stun.l.google.com:19302"]  # Google's public STUN server
        ),
        RTCIceServer(
            urls=["stun:stun.relay.metered.ca:80"]  # Metered relay STUN server
        ),
        RTCIceServer(
            urls=["turn:global.relay.metered.ca:80"],  # TURN server with plain transport
            username=auth_details["username"],
            credential=auth_details["credential"]
        ),
        RTCIceServer(
            urls=["turn:global.relay.metered.ca:80?transport=tcp"],  # TURN server using TCP transport
            username=auth_details["username"],
            credential=auth_details["credential"]
        ),
        RTCIceServer(
            urls=["turn:global.relay.metered.ca:443"],  # TURN server on port 443 for secure connections
            username=auth_details["username"],
            credential=auth_details["credential"]
        ),
        RTCIceServer(
            urls=["turns:global.relay.metered.ca:443?transport=tcp"],  # Secure TURN server with TCP transport
            username=auth_details["username"],
            credential=auth_details["credential"]
        ),
    ]
)

def create_peer_connection(cam_track):
    """
    Create and return a new RTCPeerConnection instance with the provided camera track.

    Parameters:
    - cam_track: A video track (usually representing a camera source) that is to be added to the peer connection.
    """
    global ice_config
    # Initialize the RTCPeerConnection with the defined ICE configuration
    pc = RTCPeerConnection(configuration=ice_config)
    
    # Reset the camera track to ensure it starts from a known state
    cam_track.reset()
    # Add the camera track to the RTCPeerConnection
    pc.addTrack(cam_track)

    # Define an event handler for when a data channel is created on the connection
    @pc.on("datachannel")
    def on_datachannel(channel):
        print("New data channel:", channel.label)

        # Define an event handler for incoming messages on this data channel
        @channel.on("message")
        def on_message(message):
            try:
                # Attempt to parse the message as JSON
                json_msg = json.loads(message)
            except:
                # If parsing fails, likely the message is binary data; log and ignore it
                print("Received non-JSON data (possibly binary chunk). Ignoring.")
                return

            # Handle the request based on the 'action' specified in the JSON message
            if json_msg["action"] == "request_latest_intrusion_videos":
                # Asynchronously send the latest intrusion videos, passing the requested amount
                asyncio.ensure_future(send_latest_intrusion_videos(channel, json_msg["amount"]))
            elif json_msg["action"] == "search_for_intrusion_videos":
                # Asynchronously perform a search for intrusion videos with the specified criteria
                asyncio.ensure_future(send_searched_intrusion_videos(channel, json_msg["objects"],
                                                                     json_msg["start_date"], json_msg["end_date"]))
            elif json_msg["action"] == "request_download":
                # Asynchronously send the file in chunks based on the filename and video player ID provided
                asyncio.ensure_future(send_file_in_chunks(channel, json_msg["filename"],
                                                          json_msg["video_player_id"]))
            elif json_msg["action"] == "request_yolox_objects":
                # Asynchronously send the list of YOLOX objects back to the requester
                asyncio.ensure_future(send_yolox_objects(channel))
    # Return the configured RTCPeerConnection
    return pc
