// Generate a list item element as an HTML string for a video entry
function create_list_item(filename, event_description, video_player_id) {
	// Return HTML template with embedded video information and control buttons
	return `
<li>
		<div class="video_info">
			<!-- Display the video file name -->
			<div class="video_name">${filename}</div>
			<div class="video_controls">
				<!-- Play button: clicking calls play_video with the filename and video player ID -->
				<div onclick="play_video('${filename}', '${video_player_id}')">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						fill="currentColor"
						class="bi bi-play-fill"
						viewBox="0 0 16 16"
					>
						<path
							d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393"
						/>
					</svg>
				</div>
				<!-- Download button: clicking calls save_video with the filename -->
				<div onclick="save_video('${filename}')">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						fill="currentColor"
						class="bi bi-download"
						viewBox="0 0 16 16"
					>
						<path
							d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5"
						/>
						<path
							d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708z"
						/>
					</svg>
				</div>
			</div>
		</div>
		<!-- Display event (scene) description -->
		<div class="video_description">
			<div class="event_badge"><div>Scene Description</div></div>
			<div>
			${event_description}
			</div>
		</div>
	</li>
`;
}

// Handle the response for intrusion videos by updating the UI list
function handle_intrusion_videos_response(videos_with_metadata, intrusion_list_id, video_player_id) {
	// Get the HTML element that will contain the list of intrusion videos
	let intrusion_list = document.getElementById(intrusion_list_id);
	// Clear any existing content before adding new list items
	intrusion_list.innerHTML = '';

	// If there are no videos, display a "No videos found" message
	if (Object.keys(videos_with_metadata).length === 0) {
		intrusion_list.innerHTML = '<h3>No videos found</h3>';
		return;
	}

	// Loop through each video entry in the videos_with_metadata object
	Object.entries(videos_with_metadata).forEach(([filename, description]) => {
		// Use the provided description if available; otherwise, use a default message
		const event_description = description.trim() ? description : 'No recognisable objects by yolox was detected.';
		// Append the new list item HTML to the intrusion list
		intrusion_list.innerHTML += create_list_item(filename, event_description, video_player_id);
	});
}

// Global object to store downloaded video data by filename.
// Each entry holds a Blob (the video file) and flags for play/save requests.
let downloaded_videos = {};
// Array to accumulate chunks of data during video download
let fileChunks = [];
// Flag to indicate if a download is currently in progress
let isDownloading = false;

// Play a video by either loading a downloaded Blob or requesting a download if not available
function play_video(filename, video_player_id) {
	// Check if the video is already downloaded and available
	if (filename in downloaded_videos && downloaded_videos[filename].blob !== null) {
		// Update the video player's title with the filename
		const title = document.getElementById(`${video_player_id}_content_title`);
		title.innerHTML = filename;
		// Set the video source to the Blob URL and play the video
		const video_player = document.getElementById(video_player_id);
		video_player.src = URL.createObjectURL(downloaded_videos[filename].blob);
		video_player.load();
		video_player.play();
		// Reset the play_requested flag after playing the video
		downloaded_videos[filename].play_requested = false;
	} else {
		// If the video entry doesn't exist, initialize it
		if (!(filename in downloaded_videos)) {
			downloaded_videos[filename] = { blob: null, play_requested: false, save_requested: false };
		}
		// Mark that playing the video has been requested
		downloaded_videos[filename].play_requested = true;
		// Request to download the video
		request_download(filename, video_player_id);
	}
}

// Save (download) a video file to the user's device
function save_video(filename) {
	// Check if the video is already downloaded
	if (filename in downloaded_videos && downloaded_videos[filename].blob !== null) {
		// Retrieve the Blob and create an object URL for it
		const blob = downloaded_videos[filename].blob;
		const url = URL.createObjectURL(blob);
		// Create an invisible anchor element to initiate the download
		const a = document.createElement('a');
		a.style.display = 'none';
		a.href = url;
		a.download = filename; // Sets the suggested file name for download
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		// Reset the save_requested flag after saving the video
		downloaded_videos[filename].save_requested = false;
		// Revoke the object URL after a short delay to free memory
		setTimeout(() => URL.revokeObjectURL(url), 100);
	} else {
		// If the video entry doesn't exist, initialize it
		if (!(filename in downloaded_videos)) {
			downloaded_videos[filename] = { blob: null, play_requested: false, save_requested: false };
		}
		// Mark that saving the video has been requested
		downloaded_videos[filename].save_requested = true;
		// Request to download the video
		request_download(filename);
	}
}

// Refresh the intrusion video list by requesting the latest videos
function refresh_list() {
	// Get the number of videos requested from the input field
	const num_intrusion_input = document.getElementById('num_intrusion');
	// Create a message payload for the request
	const message = {
		action: 'request_latest_intrusion_videos',
		amount: num_intrusion_input.value,
	};
	// Send the request over the data channel
	data_channel.send(JSON.stringify(message));
}

// Request the latest intrusion videos using the provided data channel
function request_latest_intrusion_videos(data_channel) {
	// Get the number of videos to retrieve from the input element
	const num_intrusion_input = document.getElementById('num_intrusion');
	// Build the request message with the specified amount
	const message = {
		action: 'request_latest_intrusion_videos',
		amount: num_intrusion_input.value,
	};
	// Send the request over the data channel
	data_channel.send(JSON.stringify(message));
}

// Attach an event listener to update the intrusion video list when the input value changes
document.getElementById('num_intrusion').addEventListener('change', function () {
	request_latest_intrusion_videos(data_channel);
});

// Event listener for submitting the intrusion video search form
document.getElementById('search_intrusion_form').addEventListener('submit', function (event) {
	event.preventDefault(); // Prevent the default form submission behavior

	const formData = new FormData(this);
	// Retrieve selected objects from the Choices.js multi-select (returns an array of selected values)
	const objectsValue = choices.getValue(true);
	// Get the start and end date values from the form inputs
	const startDate = formData.get('start_date');
	const endDate = formData.get('end_date');

	// Validate that at least one search criterion is provided
	if (
		(!objectsValue || objectsValue.length === 0) &&
		(!startDate || startDate.trim() === '') &&
		(!endDate || endDate.trim() === '')
	) {
		// Display an error message if no search criteria are given
		const errorEl = document.getElementById('error_message');
		errorEl.innerHTML = `							
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width="16"
			height="16"
			fill="currentColor"
			class="bi bi-exclamation-triangle-fill"
			viewBox="0 0 16 16"
		>
			<path
				d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"
			/>
		</svg>
		<span>Please provide at least one search criteria: objects, start date, or end date.</span>`;
		return; // Stop processing if validation fails
	} else {
		// Clear any previous error message
		document.getElementById('error_message').innerHTML = '';
	}

	// Build the payload with search parameters
	const data = {
		action: 'search_for_intrusion_videos',
		objects: objectsValue,
		start_date: startDate,
		end_date: endDate,
	};

	// Send the search request over the data channel
	data_channel.send(JSON.stringify(data));

	// Optionally, reset the form after submission:
	// this.reset();
});

// Request the download of a video file, optionally providing a video player ID
function request_download(filename, video_player_id = null) {
	// Clear previous file chunks and set downloading flag to true
	fileChunks = [];
	isDownloading = true;
	// Build the download request message payload
	const message = {
		action: 'request_download',
		video_player_id: video_player_id,
		filename: filename,
	};
	// Send the download request over the data channel
	data_channel.send(JSON.stringify(message));
}

// Handle the completion of a video download by combining chunks and processing playback or saving
function handle_download_completed(filename, video_player_id = null) {
	console.log('Download complete, building Blob...');
	// Combine the accumulated file chunks into a Blob representing an MP4 video
	const blob = new Blob(fileChunks, { type: 'video/mp4' });
	// Reset the file chunks and downloading flag
	fileChunks = [];
	isDownloading = false;
	// Initialize the downloaded video entry if it doesn't exist
	if (!(filename in downloaded_videos)) {
		downloaded_videos[filename] = { blob: null, play_requested: false, save_requested: false };
	}
	// Store the created Blob in the downloaded_videos object
	downloaded_videos[filename].blob = blob;
	// If play was requested and a video player ID is provided, play the video
	if (downloaded_videos[filename].play_requested && video_player_id !== null) {
		play_video(filename, video_player_id);
	}
	// If save was requested, trigger the save process
	if (downloaded_videos[filename].save_requested) {
		save_video(filename, video_player_id);
	}
}

// Initialize the multi-select dropdown for YOLOX object selection using Choices.js
const multi_object_selection = document.getElementById('multi_object_selection');
const choices = new Choices(multi_object_selection, {
	removeItemButton: true, // Allows removal of selected items
	shouldSort: false, // Keeps options in the original order
	placeholderValue: 'Click box to select objects, multiple selections allowed',
	searchEnabled: true, // Enables search functionality within the dropdown
});

// Request the list of YOLOX objects over the data channel
function request_yolox_objects(data_channel) {
	data_channel.send(
		JSON.stringify({
			action: 'request_yolox_objects',
		})
	);
}

// Handle the response containing YOLOX objects and update the multi-select choices
function handle_yolox_objects_response(yolox_objects) {
	// Map the array of object strings to an array of objects with value and label properties
	const choicesArray = yolox_objects.map((obj) => ({ value: obj, label: obj }));
	// Update the Choices.js instance with the new options without replacing existing ones
	choices.setChoices(choicesArray, 'value', 'label', false);
}
