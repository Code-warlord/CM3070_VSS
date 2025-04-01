# CM3070 - Final Project

## Reliant-Watcher: An Edge Computing-Based Indoor Video Surveillance System for Intruder Detection with Motion-Triggered Recording, Metadata Generation, and Remote Monitoring

### Template Used
Camera Surveillance System from CM3065 – Intelligent Signal Processing

---

This repository contains the work for a school project developed as part of **CM3090 - Final Project** at University of London, Goldsmiths. This project is for educational purposes only.

---

## Project Overview

### Core Functional Requirements with Domain and User Justifications

1. **Intruder Detection**  
   Reliant-Watcher will continuously monitor premises—whether private residences or small businesses—to detect unauthorized access in real-time. Immediate identification of potential security breaches will ensure rapid response capability.

2. **Automatic Video Recording upon Intrusion**  
   Given that manual surveillance is impractical, the system will automatically initiate video recording immediately upon detecting intrusion events. This functionality ensures reliable documentation, supporting later analysis or legal procedures, while eliminating the need for continuous human oversight.

3. **Robust Alerting System**  
   To facilitate swift user responses, Reliant-Watcher will send instant alerts through SMS, email, or mobile notifications whenever an intrusion is identified. Timely notifications are essential in mitigating risks and protecting valuable assets effectively.

4. **Generation of Intrusion Metadata and Contextual Alerts**  
   Understanding that not every detected movement constitutes a critical threat, the system will enrich each intrusion event with detailed metadata. It will differentiate between human intrusions and harmless movements, such as animals, enhancing situational awareness. This contextual approach enables users to prioritize actions appropriately and streamlines retrieval of relevant video evidence.

5. **Efficient Video Compression**  
   Considering scenarios with constrained storage and bandwidth, such as residential or small business deployments, Reliant-Watcher will implement advanced video compression techniques. These methods will significantly reduce file sizes without compromising video quality, optimizing storage space and operational costs.

6. **Secure Data Transmission for Remote Monitoring**  
   Reliant-Watcher will ensure that surveillance data transmitted for remote monitoring is fully encrypted. Secure data transmission safeguards sensitive video footage from unauthorized access, maintaining user privacy and trust.

7. **Object-Enhanced Video Database** *(Included based on stakeholder feedback)*  
   To address stakeholder requests for streamlined evidence retrieval, the system design includes an advanced video database enhanced with detailed object metadata. Each video segment will be systematically tagged, enabling precise searches by detected objects, dates, or times, significantly enhancing usability for both residential and business stakeholders.

8. **WebRTC-Based Real-Time Property Monitoring** *(Included based on stakeholder feedback)*  
   Responding directly to stakeholder demand for instantaneous monitoring, a WebRTC-based real-time video streaming solution is included in the design. This capability empowers users to remotely observe their premises in real-time, supporting rapid situational assessment and swift response to emerging threats.

9. **Modern User Interface Dashboard**  
   A sleek, intuitive user interface dashboard will serve as the central hub for Reliant-Watcher, designed specifically for ease-of-use across various environments. The dashboard will support:
   - Real-time rendering of live video streams for immediate situational awareness.
   - Intuitive access to historical video footage via advanced search capabilities.
   - Quick retrieval of the most recent recorded intrusion scene.

---

## Technical Design Specifications

- **Background Subtraction Algorithm:**  
  Subsense algorithm for intruder detection.

- **Object Detection Algorithm:**  
  YOLO DNN model via OpenCV `readNet` for metadata generation.

- **Data Transmission:**  
  WebRTC with encrypted connections, including TURN/STUN servers for robust connectivity under restrictive NAT settings.

- **Video Compression:**  
  FFMPEG for an optimal balance between video size and quality.

- **Database:**  
  SQLite to store recorded video paths and metadata.

- **Development Approach:**  
  Agile SDLC with Lean and MVP principles for adaptability and focused implementation.

### Programming Languages and Tools

1. **C++ with Python wrappers** for BS.
2. **Python** for object detection.
3. **HTML, JavaScript, CSS** for the dashboard.
4. **Python sqlite3** for database schema design and database creation for storage of intrusion event recorded videos.

### Software/Libraries/Cloud Services Utilized

- **OpenCV-Python:**  
  Provides powerful computer vision functions for motion detection and object recognition.

- **Pybind11:**  
  Enables seamless integration of C++ and Python for efficient algorithm implementation.

- **CMake:**  
  Manages the build process, ensuring portability and ease of project compilation.

- **aiortc:**  
  Initializes and manages WebRTC processes for remote monitoring.

- **websockets:**  
  Handles WebRTC signaling between the dependent watcher and remote web browsers.

- **Pytest:**  
  Utilized for automated testing.

- **Googletest:**  
  Employed to test the Pybind11 Python wrapper functions for the original Subsense C++ implementation.

- **Twilio:**  
  Used for SMS communication services, with functionality provided through the `twilio.rest.Client` module.

- **Pywa:**  
  Provides WhatsApp message integration.

- **Google API Libraries:**  
  - **Google API Client:** Accessed via `googleapiclient.discovery.build` for integrating with various Google services.  
  - **Google Auth Libraries:** Including `google_auth_oauthlib.flow.InstalledAppFlow` and `google.auth.transport.requests.Request` for managing authentication flows.

- **AWS Lambda:**  
  Facilitates the serverless execution of backend functions for the WebRTC signaling server.

- **AWS API Gateway:**  
  Manages API endpoints and traffic routing for remote connectivity via WebRTC signaling.

- **Metered.ca:**  
  A web service that provides STUN and TURN servers that ensure communication between the video surveillance system and the user interface dashboard.
