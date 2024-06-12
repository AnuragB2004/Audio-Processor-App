import logging
import os
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import azure.cognitiveservices.speech as speechsdk
import google.generativeai as genai
from IPython.display import Markdown
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_mail import Mail

app = Flask(__name__, static_url_path='/static')
CORS(app)  # Enable CORS for all routes

# Configure email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

mail = Mail(app)

flask_url = 'http://127.0.0.1:5000/send_email'

# Azure Speech Service credentials
speech_key = os.environ.get('SPEECH_KEY')
speech_region = os.environ.get('SPEECH_REGION')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

global_transcript = ""
speech_recognizer = None
is_recording = False


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        logging.error('No audio file provided')
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        logging.error('No audio file selected')
        return jsonify({'error': 'No audio file selected'}), 400

    # Save the uploaded file to a temporary location
    audio_file_path = 'temp_audio_file.wav'  # Adjust the path as needed
    audio_file.save(audio_file_path)
    logging.debug('File saved to: %s', audio_file_path)

    # Perform audio transcription
    transcript = speech_recognize_continuous_from_file(audio_file_path)

    if transcript:
        # Perform summarization and sentiment analysis
        summary, insights = summarize_sentiment(transcript)
        return jsonify({'transcript': transcript, 'summary': summary, 'insights': insights}), 200
    else:
        return jsonify({'error': 'Failed to transcribe audio'}), 500


@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.json
    email = data.get('email')
    transcript = data.get('transcript')
    summary = data.get('summary')
    insights = data.get('insights')

    if not email or not transcript or not summary or not insights:
        return jsonify({'error': 'Missing required fields'}), 400

    subject = "Your Transcription, Summary, and Sentiment Analysis"
    body = f"""
        Transcript:
        {transcript}

        Summary:
        {summary}

        Insights:
        {insights}
        """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Create SMTP session for sending the email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable security
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, email, text)
        server.quit()

        return jsonify({'message': 'Email sent successfully!'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500


@app.route('/recognize_continuous_async', methods=['POST'])
def recognize_continuous_async():
    global is_recording, speech_recognizer, global_transcript
    action = request.json.get('action')
    logging.debug(f'Received action: {action}')

    if action == 'start':
        if not is_recording:
            global_transcript = ""  # Reset transcript on start
            start_recognition()
            is_recording = True
            logging.debug('Started recognition')
            return jsonify({'message': 'Recognition started'}), 200
        else:
            return jsonify({'error': 'Recognition already started'}), 400

    elif action == 'stop':
        if is_recording:
            result = stop_recognition()
            is_recording = False
            logging.debug(f'Stopped recognition, transcript: {result.get("transcript")}')
            if result.get('transcript'):
                return jsonify({'transcript': result.get('transcript'), 'summary': result.get('summary'),
                                'insights': result.get('insights')}), 200
            else:
                return jsonify({'error': 'No transcript available'}), 500
        else:
            return jsonify({'error': 'Recognition not started'}), 400

    else:
        logging.error('Invalid action received')
        return jsonify({'error': 'Invalid action'}), 400


def start_recognition():
    global speech_recognizer

    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        def handle_final_result(evt):
            global global_transcript
            global_transcript += evt.result.text
            logging.debug(f"Recognized text: {evt.result.text}")

        def handle_stop_continuous_recognition(evt):
            logging.debug("Continuous recognition stopped.")

        speech_recognizer.recognized.connect(handle_final_result)
        speech_recognizer.session_stopped.connect(handle_stop_continuous_recognition)

        logging.debug("Speak into your microphone...")

        speech_recognizer.start_continuous_recognition_async()
    except Exception as e:
        logging.error(f"Error starting continuous recognition: {e}")


def stop_recognition():
    global global_transcript, speech_recognizer

    if speech_recognizer:
        try:
            stop_future = speech_recognizer.stop_continuous_recognition_async()
            stop_future.get()  # Ensure the stop operation is completed
            speech_recognizer = None  # Ensure the recognizer is reset
        except Exception as e:
            logging.error(f"Error stopping continuous recognition: {e}")
            return {'transcript': '', 'error': str(e)}

    if global_transcript:
        try:
            summary, insights = process_transcript(global_transcript)
            return {'transcript': global_transcript, 'summary': summary, 'insights': insights}
        except Exception as e:
            logging.error(f"Error processing transcript: {e}")
            return {'transcript': global_transcript, 'error': str(e)}
    else:
        return {'transcript': ''}


def process_transcript(transcript):
    summary, insights = summarize_sentiment(transcript)
    return summary, insights


def speech_recognize_continuous_from_file(audio_file_path):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return 'No speech could be recognized.'
        elif result.reason == speechsdk.ResultReason.Canceled:
            return 'Speech recognition canceled: {}'.format(result.cancellation_details.reason)
    except Exception as e:
        return 'Error recognizing speech from file: {}'.format(str(e))


def summarize_sentiment(text):
    try:
        def to_markdown(text):
            text = text.replace('•', '  *')
            return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

        GOOGLE_API_KEY = os.getenv('AIzaSyDg2aslIbqASRApA99owC8Kyr78sIMDo58')
        genai.configure(api_key='AIzaSyDg2aslIbqASRApA99owC8Kyr78sIMDo58')
        generation_config = {"temperature": 0.1, "top_p": 1, "top_k": 1, "max_output_tokens": 2048}

        model = genai.GenerativeModel('gemini-pro', generation_config=generation_config)

        response1 = model.generate_content("Summarize this conversation in 100 words: " + str(text))
        response2 = model.generate_content(
            "Perform sentiment analysis on this conversation (heading- sentiment analysis); Give insights on how the agent can better help/converse with the customer (heading- insights); Draft a simple email response that could be sent to the customer (heading- email response); Around 200 words, everything in points" + str(
                text))
        response2 = response2.text
        response1 = response1.text
        start = (response2.find('Sentiment Analysis'))
        end = start + len('Setniment analysis')
        text = response2[start:end + 1] + "\n" + response2[end + 1:]
        start = (response2.find('Insights'))
        end = start + len('insights')
        text = response2[:start - 3] + "\n\n" + response2[start:]
        start = (response2.find('Email Response'))
        end = start + len('email response')
        text = response2[:start - 3] + "\n\n" + response2[start:]
        for i in range(len(response2)):
            if i == end:
                response2 = response2[:i] + "\n" + response2[i:]
            if response2[i] == '-':
                response2 = response2[:i] + "\n" + response2[i + 1:]
        response2 = response2.replace("##", "\n")
        response2 = response2.replace("**", "\n")
        anslist = [response1, response2]
        return anslist
    except Exception as e:
        logging.error(f"Error summarizing sentiment: {str(e)}")
        return ["Failed to summarize sentiment", "Failed to summarize sentiment"]


if __name__ == '__main__':
    app.run(debug=True)
