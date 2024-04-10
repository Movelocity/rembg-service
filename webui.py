import os, io
import zipfile
import time
import gradio as gr
from session_factory import new_session  # 加载一些 onnx 模型
from PIL import Image
from PIL.Image import Image as PILImage
# from log_util import logger

# markdown 文本，用于展示
model_hint = """
**如果抠图效果不佳, 请手动在左侧切换模型**
- `silueta`: 通用抠图模型，速度和质量都不错
- `isnet-general-use`: 比较新的通用抠图模型
- `isnet-anime`: 针对动画人物
- `u2net`: 和 silueta 相同, 但是速度和质量不如 silueta
- `u2netp`: u2net 的轻量级版本, 速度更快
- `u2net_human_seg`: 针对人像
- `u2net_cloth_seg`: 针对衣服
- `rmbg14`: 速度较慢，但是效果好

如果抠图没抠干净，可以将结果图重新上传，换个模型进行回炉处理
"""
model_options = ['silueta', 'isnet-general-use', 'isnet-anime', 'u2net', 'u2netp', 'u2net_human_seg', 'u2net_cloth_seg', 'rmbg14']
model_dict = {name: None for name in model_options}
# TODO: 如果某些模型使用频率不高，主动释放对应的内存

def get_masked_img(model, img:PILImage) -> PILImage:
    """图像蒙版预测，输出图片通道为 RGBA """
    mask = model.predict(img)[0]  # 模型预测蒙版，图像大小缩放的逻辑已内置
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    if mask.mode != 'L':
        mask = mask.convert('L')
    img.putalpha(mask)
    return img

def handle_up_image(pil_img, model_str="silueta"):
    """处理上传文件的逻辑，参数个数和返回的长度对应 gradio 中绑定的 inputs 和 outputs"""
    if not pil_img:
        return None
    print('using: ', model_str)

    if model_str not in model_options:
        return None
    
    try:
        t1 = time.time()
        if not model_dict[model_str]:
            model_dict[model_str] = new_session(model_str)
        masked_image = get_masked_img(model_dict[model_str], pil_img)
        t2 = time.time()
        print(f'delta time: {t2-t1}')
        return masked_image
    except Exception as e:
        print(e)
        return None

def base_png(image_dir):
    """/path/to/your/file.txt => file.png"""
    base = os.path.basename(image_dir).split('.')[0]
    return base + ".png"

def batch_infer(imgs, model_str="silueta"):
    pass

def multiple_files(files, tmp):
    # All files are images
    if not files:
        return None
    
    bytesIO_images = []
    for f in files:
        # Open the image and handle it
        pil_img = Image.open(f.name)
        out_img = handle_up_image(pil_img)

        # 将处理结果保存在内存中
        img_bytes = io.BytesIO()
        out_img.save(img_bytes, format='PNG')

        # Append the image
        bytesIO_images.append((base_png(f.name), img_bytes))
        
    # zip文件命名为 {begin}-{end}.zip
    folder = os.path.dirname(files[0].name)
    begin = os.path.basename(files[0].name).split('.')[0][:7]
    end = os.path.basename(files[-1].name).split('.')[0][:7]
    zip_path = os.path.join(folder, f'{begin}-{end}.zip')
    
    # 写入zip文件
    with zipfile.ZipFile(zip_path, 'w') as myzip:
        for name, bimg in bytesIO_images:
            # Write BytesIO object to zip file
            bimg.seek(0) # go to the start of the BytesIO object
            myzip.writestr(name, bimg.read()) 

    # 临时文件不用保存
    for f in files:
        os.remove(f.name)
    return zip_path

css = """
#preview_origin, #preview_result, #preview_origin img, #preview_result img {height: 70vh !important; }

#preview_result {background: url(http://112.74.74.13:7901/pics/grids.jpg);}
"""

# Create the Gradio interface
with gr.Blocks(css=css) as app:
    with gr.Tab(label='在线抠图'):
        with gr.Row(elem_id='restricted-height'):
            origin_image = gr.Image(label='origin', elem_id='preview_origin', type="pil")
            result_image = gr.Image(label='result', elem_id='preview_result', image_mode='RGBA')
        with gr.Row():
            select_model = gr.Radio(label="抠图模型", choices=model_options, value=model_options[0])
            model_hint = gr.Markdown(value=model_hint)
            # retry_btn = gr.Button('回炉重抠')
    origin_image.change(fn=handle_up_image, inputs=[origin_image, select_model], outputs=[result_image])
    select_model.change(fn=handle_up_image, inputs=[origin_image, select_model], outputs=[result_image])

    with gr.Tab(label='批处理'):
        with gr.Row():
            files_in = gr.File(label="拖入多个文件", show_label=True, file_count='multiple', file_types=['image'], type='filepath', interactive=True)
            files_out = gr.File(label='输出', visible=True)
        with gr.Row():
            select_model2 = gr.Radio(label="抠图模型", choices=[model_options[0]], value=model_options[0])
    files_in.change(fn=multiple_files, inputs=[files_in, select_model2], outputs=[files_out])

app.launch(
    server_name="0.0.0.0",
    inbrowser=True,  # 自动打开浏览器
    share=False,
    server_port=8080,
    quiet=True
)