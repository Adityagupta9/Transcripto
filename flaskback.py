import os
from flask import Flask, render_template, request, redirect, url_for, send_file
import whisperx
import cv2
from moviepy.editor import VideoFileClip

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
TRANSCRIPT_FOLDER = 'static/transcripts/'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TRANSCRIPT_FOLDER'] = TRANSCRIPT_FOLDER

device = "cpu"
batch_size = 16
compute_type = "int8"

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        selected_model = request.form.get('model', 'large-v2')
        
        if file:
            video_file = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(video_file)

            audio_file = video_file.replace(".mp4", ".mp3")
            video_clip = VideoFileClip(video_file)
            video_clip.audio.write_audiofile(audio_file)
            video_clip.close()

            audio = whisperx.load_audio(audio_file)
            model = whisperx.load_model(selected_model, device, compute_type=compute_type)
            result = model.transcribe(audio, batch_size=batch_size)

            model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
            result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

            diarize_model = whisperx.DiarizationPipeline(use_auth_token=HUGGINGFACE_TOKEN, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)

            labeled_frames = process_video(video_file, result)
            transcript, labeled_frames_list = format_transcription(result, labeled_frames)

            transcript_file_path = save_transcript_to_file(transcript, file.filename)

            return render_template("result.html", transcript=transcript, labeled_frames=labeled_frames_list, transcript_file_path=transcript_file_path)

    return render_template("index.html")

def process_video(video_file, result):
    cap = cv2.VideoCapture(video_file)
    first_speaker_occurrences = {}
    labeled_frames = {}

    for segment in result["segments"]:
        if 'speaker' not in segment:
            print("Warning: 'speaker' key missing in segment.")
            continue

        speaker_id = segment['speaker']
        if speaker_id not in first_speaker_occurrences:
            first_speaker_occurrences[speaker_id] = segment['start']
            timestamp = segment['start']
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()

            if ret:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(frame, f"Speaker {speaker_id}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

                image_filename = f"static/images/labeled_frame_speaker_{speaker_id}.jpg"
                cv2.imwrite(image_filename, frame)
                labeled_frames[speaker_id] = image_filename

    cap.release()
    return labeled_frames

def format_transcription(result, labeled_frames):
    formatted_transcription = []
    labeled_frames_list = []
    seen_speakers = set()

    for segment in result["segments"]:
        if 'speaker' not in segment:
            print("Warning: 'speaker' key missing in segment.")
            continue

        speaker = f"SPEAKER_{segment['speaker']}"
        timestamp = segment['start']
        formatted_time = f"{int(timestamp // 3600):02}:{int((timestamp % 3600) // 60):02}:{int(timestamp % 60):02}"
        text = segment['text']
        
        formatted_transcription.append({
            "speaker": speaker,
            "timestamp": formatted_time,
            "text": text
        })

        if segment['speaker'] not in seen_speakers and segment['speaker'] in labeled_frames:
            labeled_frames_list.append({
                'speaker': speaker,
                'image_path': labeled_frames[segment['speaker']]
            })
            seen_speakers.add(segment['speaker'])

    return formatted_transcription, labeled_frames_list

def save_transcript_to_file(transcript, filename):
    transcript_file_path = f"./static/transcripts/{filename}_transcript.txt"
    
    with open(transcript_file_path, 'w', encoding='utf-8') as f:
        for segment in transcript:
            f.write(f"{segment['speaker']} {segment['timestamp']}\n") 
            f.write(f"{segment['text']}\n\n")  
    
    return transcript_file_path

@app.route("/download/<path:filename>")
def download_file(filename):
    """Download the transcript file."""
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
