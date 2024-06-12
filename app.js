document.addEventListener('DOMContentLoaded', function() {
    // Initialize emailjs if needed
    // emailjs.init("YOUR_USER_ID");

    let isRecording = false;

    // Upload audio file
    document.getElementById('upload-audio').addEventListener('change', function(event) {
        const audioFile = event.target.files[0];
        if (!audioFile) {
            alert('Please select an audio file.');
            return;
        }

        const formData = new FormData();
        formData.append('audio_file', audioFile);

        const spinner = document.getElementById('loading-spinner');
        spinner.style.display = 'block';

        const xhr = new XMLHttpRequest();

        xhr.addEventListener('load', function(event) {
            const response = JSON.parse(xhr.responseText);
            updateOutput(response);
            spinner.style.display = 'none';
        });

        xhr.addEventListener('error', function(event) {
            console.error('Error uploading file');
            spinner.style.display = 'none';
        });

        xhr.open('POST', '/transcribe');
        xhr.send(formData);
    });

    // Start/Stop recording
    document.getElementById('start-recording').addEventListener('click', function() {
        console.log('Start recording button clicked');
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    function startRecording() {
        console.log('Starting recording...');
        isRecording = true;
        document.getElementById('start-recording').innerText = 'Stop Recording';
        document.getElementById('mic-icon').style.display = 'inline-block';
        document.getElementById('loading-spinner').style.display = 'none';

        fetch('/recognize_continuous_async', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'start' })
        }).then(response => {
            console.log('Start recording response received');
            if (!response.ok) {
                throw new Error('Failed to start recording');
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('Error starting recording: ' + error.message);
        });
    }

    function stopRecording() {
        console.log('Stopping recording...');
        isRecording = false;
        document.getElementById('start-recording').innerText = 'Start Recording';
        document.getElementById('mic-icon').style.display = 'none';
        document.getElementById('loading-spinner').style.display = 'block';

        fetch('/recognize_continuous_async', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'stop' })
        }).then(response => response.json()).then(data => {
            console.log('Stop recording response received', data);
            if (data.transcript) {
                updateOutput(data);
            } else if (data.error) {
                console.error('Error:', data.error);
                alert('Error stopping recording: ' + data.error);
                document.getElementById('loading-spinner').style.display = 'none';
            } else {
                console.error('No transcript available');
                document.getElementById('loading-spinner').style.display = 'none';
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('Error stopping recording: ' + error.message);
            document.getElementById('loading-spinner').style.display = 'none';
        });
    }

    function updateOutput(data) {
        if (data.transcript) {
            document.getElementById('transcript-text').innerText = data.transcript;
        }
        if (data.summary) {
            document.getElementById('summary-text').innerText = data.summary;
        }
        if (data.insights) {
            document.getElementById('insights-text').innerText = data.insights;
        }

        document.getElementById('input-screen').style.display = 'none';
        document.getElementById('output-screen').style.display = 'block';
        document.getElementById('loading-spinner').style.display = 'none';
    }

    // Send email
    document.getElementById('send-email').addEventListener('click', function() {
        const email = document.getElementById('email-input').value;
        const transcript = document.getElementById('transcript-text').innerText;
        const summary = document.getElementById('summary-text').innerText;
        const insights = document.getElementById('insights-text').innerText;

        if (!email || !transcript || !summary || !insights) {
            alert('All fields are required');
            return;
        }

        const data = {
            email: email,
            transcript: transcript,
            summary: summary,
            insights: insights
        };

        fetch('/send_email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }).then(response => response.json()).then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert('Email sent successfully!');
            }
        }).catch(error => {
            console.error('Error:', error);
        });
    });

    // Additional logging for troubleshooting
    console.log('DOM fully loaded and parsed');
});
