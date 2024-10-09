from flask import Flask, request, render_template, jsonify
import os
import moviepy.editor as mp
import whisper
import threading

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Store transcription status
transcription_status = {
    'processing': False,
    'completed': False,
    'model_name': '',
    'result': ''
}

# Load Whisper model
model_cache = {}

def get_model(model_name):
    if model_name not in model_cache:
        model_cache[model_name] = whisper.load_model(model_name)
    return model_cache[model_name]

def transcribe_audio(audio_path, model_name):
    model = get_model(model_name)
    result = model.transcribe(audio_path)
    return result

def format_transcription(transcription_result):
    formatted_output = []
    for idx, segment in enumerate(transcription_result['segments']):
        start_time = segment['start']
        formatted_time = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02}"
        speaker = f"Speaker {idx % 2 + 1}"
        formatted_output.append(f'<div class="line"><span class="timestamp">{formatted_time}</span> {speaker}: {segment["text"].strip()}</div>')
    return "".join(formatted_output)

def run_transcription(file_path, model_name):
    global transcription_status
    transcription_status['processing'] = True
    transcription_status['completed'] = False

    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio.mp3')
    video = mp.VideoFileClip(file_path)
    video.audio.write_audiofile(audio_path)

    transcription_result = transcribe_audio(audio_path, model_name)
    formatted_transcription = format_transcription(transcription_result)

    transcription_status['result'] = formatted_transcription
    transcription_status['completed'] = True
    transcription_status['processing'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['video']
    if file.filename == '':
        return "No selected file", 400

    input_video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'input_video.mp4')
    file.save(input_video_path)

    model_name = request.form.get('model', 'base')

    threading.Thread(target=run_transcription, args=(input_video_path, model_name)).start()

    return jsonify({'status': 'processing'})

@app.route('/status', methods=['GET'])
def check_status():
    return jsonify(transcription_status)

@app.route('/transcript', methods=['GET'])
def transcript():
    return render_template('result.html', transcription=transcription_status['result'])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
