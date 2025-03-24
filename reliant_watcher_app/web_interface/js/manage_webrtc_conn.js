// Establish a WebSocket connection to the specified URL
const ws = new WebSocket('wss://gjtxmivc5m.execute-api.us-east-1.amazonaws.com/production/');

// WebSocket Event: Connection Opened
ws.onopen = function () {
	// Prepare connection message to send once WebSocket is open
	const message = {
		step: '1_connect',
		id: 'web_interface',
	};
	// Send connection message in JSON format
	ws.send(JSON.stringify(message));

	// After establishing connection, initiate sending a WebRTC offer
	send_offer();
};

// ICE Server configuration for establishing WebRTC connection
const iceConfig = {
	iceServers: [
		{
			// Google STUN server for NAT traversal
			urls: ['stun:stun.l.google.com:19302'],
		},
		{
			// Additional STUN server from metered.ca
			urls: ['stun:stun.relay.metered.ca:80'],
		},
		{
			// TURN server configuration with provided credentials
			urls: ['turn:global.relay.metered.ca:80'],
			username: username,
			credential: credential,
		},
		{
			// TURN server configuration using TCP transport
			urls: ['turn:global.relay.metered.ca:80?transport=tcp'],
			username: username,
			credential: credential,
		},
		{
			// TURN server on port 443 for secured connections
			urls: ['turn:global.relay.metered.ca:443'],
			username: username,
			credential: credential,
		},
		{
			// Secure TURN server using TLS and TCP transport
			urls: ['turns:global.relay.metered.ca:443?transport=tcp'],
			username: username,
			credential: credential,
		},
	],
};

// Function to create a new RTCPeerConnection and associated Data Channel
function create_peer_connection() {
	// Initialize RTCPeerConnection with ICE configuration
	let pc = new RTCPeerConnection(iceConfig);

	// Create a Data Channel named 'data_channel' for sending/receiving non-media data
	let dc = pc.createDataChannel('data_channel');

	// Event handler: Data Channel opened successfully
	dc.onopen = () => {
		// When data channel is open, request YOLOX object detection results and intrusion videos
		request_yolox_objects(dc);
		request_latest_intrusion_videos(dc);
	};

	// Event handler: Data Channel closed
	dc.onclose = () => {
		console.log('Data Channel Closed!');
	};

	// Event handler: Data Channel encountered an error
	dc.onerror = (error) => {
		console.error('Data Channel Error:', error);
	};

	// Event handler: Message received on the Data Channel
	dc.onmessage = (event) => {
		// Check if the received data is a string
		if (typeof event.data === 'string') {
			const data = JSON.parse(event.data);
			// Process actions based on the "action" property in the received message
			if (data.action === 'send_latest_intrusion_videos') {
				// Handle response for the latest intrusion videos request
				handle_intrusion_videos_response(
					data.videos_with_metadata,
					'recent_intrusion_list',
					'recent_intrusion_video_player'
				);
			} else if (data.action === 'send_searched_intrusion_videos') {
				// Handle response for searched intrusion videos request
				handle_intrusion_videos_response(
					data.videos_with_metadata,
					'search_intrusion_list',
					'searched_intrusion_video_player'
				);
			} else if (data.action === 'download_complete') {
				// Handle successful file download completion
				handle_download_completed(data.filename, data.video_player_id);
			} else if (data.action === 'download_error') {
				// Alert user if there was an error during file transfer
				alert('File transfer error: ' + data.message);
				isDownloading = false;
				fileChunks = [];
			} else if (data.action === 'send_yolox_objects') {
				// Process YOLOX object detection results
				handle_yolox_objects_response(data.yolox_objects);
			} else if (data.action === 'error') {
				// Alert user if any error message is received
				alert('Error: ' + data.error_message);
			}
		} else {
			// Likely received binary data (ArrayBuffer or Blob)
			if (isDownloading) {
				// Append binary data to fileChunks array if a download is in progress
				fileChunks.push(event.data);
			} else {
				console.warn("Received binary data, but not in 'isDownloading' state.");
			}
		}
	};

	// Event handler: Incoming media stream (e.g., video tracks)
	pc.ontrack = (event) => {
		if (event.streams.length > 0) {
			// If a media stream is received, attach it to the video element for livestreaming
			const remote_stream = event.streams[0];
			const livestream_video = document.getElementById('livestream_video');
			livestream_video.srcObject = remote_stream;
			livestream_video.play();
		}
	};

	// Event handler: ICE candidate generated for NAT traversal
	pc.onicecandidate = (event) => {
		if (event.candidate) {
			// Store candidate information
			const candidate_info = event.candidate;
			// Build a simplified ICE candidate object
			const ice_candidate = {
				component: candidate_info.component.toLowerCase() === 'rtp' ? 1 : 2,
				foundation: candidate_info.foundation,
				address: candidate_info.address,
				port: candidate_info.port,
				priority: candidate_info.priority,
				protocol: candidate_info.protocol,
				type: candidate_info.type,
				relatedAddress: candidate_info.relatedAddress,
				relatedPort: candidate_info.relatedPort,
				sdpMid: candidate_info.sdpMid,
				sdpMLineIndex: candidate_info.sdpMLineIndex,
				tcpType: candidate_info.tcpType,
			};
			// Send ICE candidate information to the server via WebSocket
			ws.send(
				JSON.stringify({
					step: '3_send_offer_ice',
					ice_candidate: JSON.stringify(ice_candidate),
				})
			);
		}
	};

	// Return the peer connection and data channel for further use
	return { pc, dc };
}

// Create a new peer connection and data channel; destructure results into variables
let { pc: web_interface_pc, dc: data_channel } = create_peer_connection();

// WebSocket Event: Message Received from the server
ws.onmessage = function (event) {
	try {
		const data = JSON.parse(event.data);
		// Process the message based on its "step" field
		if (data['step'] === '1_connect') {
			console.log('1. Response Received:', JSON.stringify(data));
		} else if (data['step'] === '2_send_offer') {
			console.log('2. Offer Response Received:');
		} else if (data['step'] === '3_send_offer_ice') {
			console.log('3. ICE Feedback Response Received:');
		} else if (data['step'] === '4_send_answer') {
			// Set the remote description with the answer received from the server
			web_interface_pc
				.setRemoteDescription(new RTCSessionDescription(data['answer']))
				.then(() => {
					console.log('4. Answer SDP set successfully!');
				})
				.catch((error) => console.error('Error setting remote description:', error));
		}
	} catch (error) {
		// Log any errors that occur while processing the incoming message
		console.error('Error processing WebSocket message:', error);
	}
};

// Function to close the WebSocket connection
function disconnect() {
	ws.close();
}

// WebRTC: Create Data Channel and Send Offer
async function send_offer() {
	try {
		// Create an SDP offer that includes video reception capability
		const offer = await web_interface_pc.createOffer({ offerToReceiveVideo: true });
		// Set the local description to the created offer
		await web_interface_pc.setLocalDescription(offer);
		// Construct the offer message to send to the server
		const offerMessage = {
			step: '2_send_offer',
			offer: JSON.stringify(offer),
		};
		// Ensure the WebSocket is open before sending the offer
		if (typeof ws !== 'undefined' && ws.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify(offerMessage));
		} else {
			console.error('WebSocket connection is not open.');
		}
	} catch (error) {
		// Log any errors that occur during offer creation or sending
		console.error('Error creating or sending offer:', error);
	}
}
