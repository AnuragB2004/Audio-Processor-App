# Audio Processor App

## Overview

Audio Processor App is a web-based application that allows users to upload, record, and process audio files. The app transcribes audio to text, summarizes the content, and extracts key insights. Additionally, users can send the processed information via email.

## Features

- **Upload Audio Files**: Supports uploading of audio files for transcription.
- **Record Audio**: Allows users to record audio directly within the app.
- **Real-Time Transcription**: Converts spoken words into text in real time.
- **Content Summary and Insights**: Summarizes the transcribed text and provides key insights.
- **Email Integration**: Sends the transcribed text, summary, and insights to a specified email address.

## Setup

### Prerequisites

- Node.js
- npm (Node Package Manager)
- Python (for backend processing if needed)

### Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yAnuragB2004/Audio-Processor-App.git
    cd Audio-Processor-App
    ```

2. **Install frontend dependencies**:
    ```sh
    cd frontend
    npm install
    ```

3. **Install backend dependencies** (if applicable):
    ```sh
    cd backend
    pip install -r requirements.txt
    ```

### Configuration

- **EmailJS Initialization**: Replace `YOUR_USER_ID` in `app.js` with your EmailJS user ID.
- **Backend Configuration**: Ensure your backend server is set up to handle `/transcribe`, `/recognize_continuous_async`, and `/send_email` endpoints.

## Usage

1. **Start the frontend server**:
    ```sh
    cd frontend
    npm start
    ```

2. **Start the backend server**:
    ```sh
    cd backend
    python backend.py
    ```

3. **Access the app**:
    Open your web browser and navigate to `http://localhost:3000`.

### How to Use

- **Upload Audio File**:
    - Click on the "Upload Audio" button.
    - Select an audio file from your device.
    - Wait for the file to be processed and the transcript to be displayed.

- **Record Audio**:
    - Click on the "Start Recording" button.
    - Speak into your microphone.
    - Click the "Stop Recording" button to end the recording and process the audio.

- **Send Email**:
    - After processing the audio, enter your email address in the provided field.
    - Click the "Send Email" button to send the transcript, summary, and insights to your email.

## Video Tutorial

For a detailed video tutorial on how to set up and use the Audio Processor App, watch the video attached.

https://github.com/AnuragB2004/Audio-processor-App/assets/105806479/5ebeab19-62f7-46bf-a8b3-13695593db5a

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, please contact [your email](anuragdgp@gmail.com).

