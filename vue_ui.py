from flask import Flask, send_from_directory, send_file, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sessions import new_session
from PIL import Image
from io import BytesIO  # 文件写在内存里，不用经过硬盘
from zipfile import ZipFile
import os

app = Flask(__name__, static_folder='app/dist')
CORS(app)

# upload folder configuration 
app.config['UPLOAD_FOLDER'] = 'uploads'

model_options = [
    'silueta', 'isnet-general-use', 'isnet-anime', 
    'u2net', 'u2netp', 'u2net_human_seg', 'u2net_cloth_seg', 
    'rmbg14'
]
model_dict = {name: None for name in model_options}
def get_model(model_str):
    if model_str not in model_options:
        raise ValueError("model not supported")
    if not model_dict[model_str]:
        model_dict[model_str] = new_session(model_str)
    return model_dict[model_str]

##############  html 前端服务 ################
@app.route('/html')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/html/<path:filename>')
def public_files(filename):
    """
    app.static_folder 默认是 /static/
    """
    print(f"visit ==> {filename}")
    return send_from_directory(app.static_folder, filename)

##################   API    ###################
@app.route('/v1/rembg', methods=['POST'])
def rembg():
    model = request.form['model']
    file = request.files['file']
    file_count = request.form.get('count', type=int)

    # Confirming received data
    print(f"Model: {model}, File count: {file_count}")
    
    # Read the zip file from request and get the filenames and sizes
    masks = []
    zipfile = ZipFile(file.stream, 'r')
    for filename in zipfile.namelist():
        content = zipfile.read(filename)
        print(f"File name: {filename} - File size: {len(content)} bytes")
        pil_img = Image.open(content)
        mask:Image.Image = get_model(model).predict(pil_img)[0]
        
        masks.append(BytesIO.write())
        
    # Creating a new BytesIO object and writing a new zip file
    data = BytesIO()
    with ZipFile(data, 'w') as zip:
        for filename in zipfile.namelist():
            zip.writestr(filename, zipfile.read(filename))

    data.seek(0)  # Make sure to reset the pointer to the start of the stream
    return send_file(data, mimetype='application/zip', as_attachment=True, download_name="rearranged.zip")


@app.route('/v1/replace_bg', methods=['POST'])
def replace_background():
    if 'bg_file' not in request.files or 'fg_file' not in request.files:
        return jsonify({'error': 'No file part.'}), 400
    model = request.form.get('model')
    type = request.form.get('type')
    accept = request.form.get('accept')
    bg_file = request.files['bg_file']
    fg_file = request.files['fg_file']

    if bg_file.filename == '' or fg_file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400
    if bg_file and fg_file:
        bg_filename = secure_filename(bg_file.filename)
        fg_filename = secure_filename(fg_file.filename)
        # bg_file.save(os.path.join(app.config['UPLOAD_FOLDER'], bg_filename))
        # fg_file.save(os.path.join(app.config['UPLOAD_FOLDER'], fg_filename))

    # your code to replace background

    return jsonify({'message': 'Successful.'}), 200


@app.route('/v1/model_list', methods=['GET'])
def get_model_list():
    # your code to get model list
    models = ["model1", "model2", "model3"]
    return jsonify({'models': models}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8088)
