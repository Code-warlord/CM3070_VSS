import asyncio  # For asynchronous programming and handling I/O without blocking
import websockets  # Library for WebSocket communication
from websockets.asyncio.client import connect  # Provides an async context manager for WebSocket connections
import json  # For encoding and decoding JSON messages
from aiortc import RTCSessionDescription, RTCIceCandidate  # For handling WebRTC session descriptions and ICE candidates
import socket  # For handling network-related errors
from . import webrtc_channels_management as WCM  # Module for managing WebRTC channels and RTCPeerConnections
from .exchange_with_UI import send_latest_intrusion_videos, send_file_in_chunks, \
                                send_searched_intrusion_videos, send_yolox_objects  # Functions for UI communication

# Callback function triggered when the WebSocket connection is established.
# It sends an initial "1_connect" message to notify the server of the connection.
async def on_open(ws):
    message = {
        "step": "1_connect",
        "id": "smart_vss",  # Identifier for this connection
    }
    await ws.send(json.dumps(message))  # Send the JSON-formatted connection message
    print("1. Message sent to the AWS Lambda server, awaiting response...")

# Callback function to handle incoming messages from the WebSocket connection.
# Processes messages based on the "step" value in the message.
async def on_message(ws, message, cam_track, loop_control):
    # Parse the incoming JSON message
    message = json.loads(message)
    # If the loop control indicates to stop, close the WebSocket connection
    if loop_control["stop"]:
        ws.close()

    # Process connection feedback messages
    if message["step"] == "1_connect":
        # Feedback from the smart_vss itself
        if message["id"] == "smart_vss":
            print(f"1. Feedback Received: {message}")
        # Feedback from the web interface
        elif message["id"] == "web_interface":
            # If an existing RTCPeerConnection exists, close it before creating a new one
            if WCM.vss_pc is not None:
                await WCM.vss_pc.close()
            # Create a new RTCPeerConnection using the provided camera track
            WCM.vss_pc = WCM.create_peer_connection(cam_track)

    # Process the offer from the server (step 2)
    elif message["step"] == "2_send_offer":
        # Debug: Print the received offer description (note: careful with nested quotes)
        # print(f'2. offer description received from the AWS Lambda server. offer = {message["offer"]}')
        offer = json.loads(message["offer"])
        # Set the remote description on the existing RTCPeerConnection using the received offer
        await WCM.vss_pc.setRemoteDescription(
            RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        )
        # Create an answer to the offer
        answer = await WCM.vss_pc.createAnswer()
        await WCM.vss_pc.setLocalDescription(answer)
        
        # Prepare the answer message to send back to the server
        answer_msg_to_send = {
            "step": "4_send_answer",
            "answer": {
                "sdp": WCM.vss_pc.localDescription.sdp,
                "type": WCM.vss_pc.localDescription.type
            }
        }
        await ws.send(json.dumps(answer_msg_to_send))
        print("4. Answer SDP sent to the AWS Lambda server, awaiting response...")

    # Process ICE candidate messages (step 3)
    elif message["step"] == "3_send_offer_ice":
        # print(f"3. Ice candidates received from the AWS Lambda server. candidates = {message['ice_candidate']}")
        candidate_info = json.loads(message["ice_candidate"])
        # Create an RTCIceCandidate object from the received candidate information
        candidate = RTCIceCandidate(
            port=candidate_info.get("port"),          foundation=candidate_info.get("foundation"),
            ip=candidate_info.get("address"),         component=candidate_info.get("component"),        
            priority=candidate_info.get("priority"),    protocol=candidate_info.get("protocol"),
            type=candidate_info.get("type"),            relatedAddress=candidate_info.get("relatedAddress"),
            sdpMid=candidate_info.get("sdpMid"),        relatedPort=candidate_info.get("relatedPort"),      
            tcpType=candidate_info.get("tcpType"),      sdpMLineIndex=candidate_info.get("sdpMLineIndex")
        )
        # Add the ICE candidate to the RTCPeerConnection
        await WCM.vss_pc.addIceCandidate(candidate)
        print("3. ICE candidate added to the peer connection.")

    # Process answer feedback messages (step 4)
    elif message["step"] == "4_send_answer":
        print(f"4. Answer Feedback Received")
 
# Main asynchronous function to establish and maintain the WebSocket connection,
# handling reconnection and message processing in a loop.
async def listen(loop_control, cam_track):
    # Continue looping until loop_control indicates to stop
    while not loop_control["stop"]:
        try:
            # Attempt to connect to the WebSocket server using the specified URI
            async with connect("wss://gjtxmivc5m.execute-api.us-east-1.amazonaws.com/production/") as ws:
                # Create a new RTCPeerConnection using the provided camera track
                WCM.vss_pc = WCM.create_peer_connection(cam_track)
                # Send the initial connection message
                await on_open(ws)

                # Continuously listen for incoming messages from the server
                try:
                    async for message in ws:
                        # If loop control indicates to stop, break out of the loop
                        if loop_control["stop"]:
                            break
                        # Debug: Print the raw message received
                        print(f"======================================= {message}")
                        # Process the incoming message
                        await on_message(ws, message, cam_track, loop_control)
                # Handle unexpected connection closures gracefully
                except websockets.exceptions.ConnectionClosedError:
                    print("Connection closed unexpectedly.")
                # Catch any other exceptions that occur while listening
                except Exception as e:
                    print(f"An error occurred while listening for messages: {e}")
                finally:
                    # Wait for 10 seconds before attempting to reconnect
                    await asyncio.sleep(10)
        # Handle various WebSocket and network errors with specific error messages
        except websockets.exceptions.InvalidURI:
            print("The WebSocket URI provided is invalid.")
        except websockets.exceptions.InvalidHandshake:
            print("The WebSocket handshake failed. Check the server or URI.")
        except socket.gaierror:
            print("Network error: Unable to resolve the server address. Are you connected to the internet?")
        except OSError as e:
            print(f"Network error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            # Inform the user and wait before retrying the connection
            print("Retrying in 10 seconds...")
            await asyncio.sleep(10)
    print("Exiting the loop...")
