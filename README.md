Transcripto
Transcripto is a transcription application that allows users to upload videos, transcribe audio with speaker labels, and view labeled images for each speaker.

Features
Transcribe video files to text with speaker labels and timestamps
Convert audio to various formats
Display speaker-labeled images after transcription
Folder Structure
plaintext
Copy code
project-folder
│
├── flaskback.py                     # Main Flask application file
├── /static
│   ├── /uploads               # Folder for uploaded videos and audio files
│   ├── /images                # Folder for speaker-labeled images
│   └── /css                   # Folder for CSS styles
│       └── style.css          # CSS file
├── /templates
│   ├── index.html             # Upload form
│   └── result.html            # Displays transcription and labeled images
Handling Large Files with Git LFS
This project uses some large files. To handle them effectively, please ensure Git Large File Storage (LFS) is set up on your machine:

Install Git LFS (if not already installed):

bash
Copy code
git lfs install
Track specific large files (replace your_large_file with actual large files in the project):

bash
Copy code
git lfs track "your_large_file"
Commit the changes:

bash
Copy code
git add .
git commit -m "Track large files with Git LFS"
Push the code to GitHub:

bash
Copy code
git push -u origin main
Pushing Changes with Large Files
In cases where large files are present, increasing Git's HTTP buffer size can help avoid push errors:

bash
Copy code
git config http.postBuffer 524288000
