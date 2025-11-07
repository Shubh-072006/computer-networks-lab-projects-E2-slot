from flask import Flask, request, render_template, send_from_directory
import os
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_file_info():
    files = os.listdir(UPLOAD_FOLDER)
    file_sizes = {}
    file_times = {}
    for f in files:
        path = os.path.join(UPLOAD_FOLDER, f)
        file_sizes[f] = round(os.path.getsize(path)/1024, 2)  # Size in KB
        file_times[f] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(path)))
    return files, file_sizes, file_times

@app.route('/')
def index():
    files, file_sizes, file_times = get_file_info()
    return render_template('index.html', files=files, file_sizes=file_sizes, file_times=file_times)

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
        uploaded_file.save(path)
    files, file_sizes, file_times = get_file_info()
    return render_template('upload_success.html', files=files, file_sizes=file_sizes, file_times=file_times)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
