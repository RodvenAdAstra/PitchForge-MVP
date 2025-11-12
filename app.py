from flask import Flask, request, render_template
from werkzeug.utils import secure_filename  # Don't forget this!
import os  # If saving files

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Optional: dir for saving files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create if needed

@app.route('/', methods=['GET', 'POST'])
def index():
    filename = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error='No file part'), 400
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file'), 400
        if file:
            filename = secure_filename(file.filename)
            # Optional: Save/process the file (e.g., for PDF pitch analysis)
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Here: Add your PitchForge logic, like extracting text from PDF
    return render_template('index.html', filename=filename)
