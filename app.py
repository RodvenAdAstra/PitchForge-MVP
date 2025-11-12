from flask import Flask, request, render_template  # Your existing imports
from werkzeug.utils import secure_filename  # Add this

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400
        if file:
            filename = secure_filename(file.filename)  # Now this works
            # Save the file or process it here, e.g.:
            # file.save(os.path.join('uploads', filename))
            return f'File uploaded: {filename}'
    return render_template('index.html')  # Or whatever your GET response is
