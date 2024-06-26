import os, io
import zipfile
import time
import gradio as gr
# from session_factory import new_session  # 加载一些 onnx 模型
from sessions import new_session
from PIL import Image
from PIL.Image import Image as PILImage
from utils.log_util import logger
from utils.injector import inject_template

inject_template()

# TODO: 由于写完日志再返回，如果日志服务有延迟，会给用户造成卡顿。需要寻找一种先给用户返回，再写日志的方案。

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

model_hint2 = """
**如果抠图效果不佳, 请手动切换模型**
- `silueta`: 通用抠图模型，速度和质量都不错
- `isnet-general-use`: 比较新的通用抠图模型
- `isnet-anime`: 针对动画人物
- `u2net`: 和 silueta 相同, 但是速度和质量不如 silueta
- `u2netp`: u2net 的轻量级版本, 速度更快
- `u2net_human_seg`: 针对人像
- `u2net_cloth_seg`: 针对衣服
- `rmbg14`: 速度较慢，但是效果好

如果抠图没抠干净，可以到抠图首页将结果图重新上传，换个模型进行回炉处理

> 返回的文件可能比上传的文件尺寸更大，是因为带透明通道的png图片压缩率不如不带透明通道的jpg图片
"""

model_options = [
    'silueta', 'isnet-general-use', 'isnet-anime',
    'u2net', 'u2netp', 'u2net_human_seg', 'u2net_cloth_seg',
    'rmbg14'
]
model_dict = {name: None for name in model_options}
# TODO: 如果某些模型使用频率不高，主动释放对应的内存

def get_model(model_str):
    if model_str not in model_options:
        raise ValueError("model not supported")
    if not model_dict[model_str]:
        model_dict[model_str] = new_session(model_str)
    return model_dict[model_str]

def put_alpha(img, mask):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    if mask.mode != 'L':
        mask = mask.convert('L')  # gray scale
    # 新生成一张全白的图，目的是把RGB通道都mask一遍，增大像素重复面积，增加图片压缩率
    white_img = Image.new('RGBA', img.size, (255, 255, 255, 255))
    # Composite the original image over the white image using the mask
    masked_img = Image.composite(img, white_img, mask)
    masked_img.putalpha(mask)
    return masked_img

def handle_single_image(pil_img, model_str="silueta"):
    """处理上传文件的逻辑，参数个数和返回的长度对应 gradio 中绑定的 inputs 和 outputs"""
    try:
        if not pil_img:
            raise ValueError("")
        start_time = time.time()
        """图像蒙版预测，输出图片通道为 RGBA """
        mask = get_model(model_str).predict(pil_img)[0]  # 模型预测蒙版，图像大小缩放的逻辑已内置
        masked_image = put_alpha(pil_img, mask)
        dt = time.time() - start_time
        logger.info(f'model: {model_str}, dt: {dt:.3f}s')
        return masked_image
    except Exception as e:
        if len(str(e))>0:
            logger.info(f"model: {model_str}, err: {e}")
        return None

def handle_img_merge(bg_img, fg_img, model_str="silueta"):
    """处理上传文件的逻辑，参数个数和返回的长度对应 gradio 中绑定的 inputs 和 outputs"""
    try:
        if not bg_img or not fg_img:
            raise ValueError("")
        if bg_img.mode != 'RGBA':
            bg_img = bg_img.convert('RGBA')
        bg_img = bg_img.resize(fg_img.size, Image.LANCZOS)

        start_time = time.time()
        """图像蒙版预测，输出图片通道为 RGBA """
        mask = get_model(model_str).predict(fg_img)[0]  # 模型预测蒙版，图像大小缩放的逻辑已内置
        masked_image = put_alpha(fg_img, mask)
        dt = time.time() - start_time

        logger.info(f'model: {model_str}, dt: {dt:.3f}s')
        return Image.alpha_composite(bg_img, masked_image)
    except Exception as e:
        if len(str(e))>0:
            logger.info(f"model: {model_str}, err: {e}")
        return None

def base_png(image_dir):
    """/path/to/your/file.txt => file.png"""
    base = os.path.basename(image_dir).split('.')[0]
    return base + ".png"

def handle_multiple_images(files, model_str="silueta"):
    # All files are images
    if not files:
        return None
    try:
        named_images = {}
        for f in files:
            # Open the image and handle it
            pil_img = Image.open(f.name)
            named_images[base_png(f.name)] = pil_img

        #===================== infer using model ============#
        start_time = time.time()
        if model_str == 'rmbg14': # batch torch infer
            masked_imgs = get_model(model_str).predict_batch(list(named_images.values()))
            for i, (k, img) in enumerate(named_images.items()):
                named_images[k] = put_alpha(img, masked_imgs[i])
                # TODO: put_alpha 这个操作在前端完成，性能提升空间很大，网络传输的数据量变为 1/4
        else:
            model = get_model(model_str)
            for name, pil_img in named_images.items():
                mask = model.predict(pil_img)[0]
                masked_image = put_alpha(pil_img, mask)
                 # 将处理结果保存在内存中 bytesiio or pils
                named_images[name] = masked_image
        dt = time.time() - start_time
        logger.info(f'model: {model_str}, imgs: {len(files)}, dt: {dt:.3f}s')
        #=====================================================#

        # zip文件命名为 {begin}-{end}.zip
        # /tmp/gradio/* 需要定期手动清理
        folder = os.path.dirname(files[0].name)
        begin = os.path.basename(files[0].name).split('.')[0][:7]
        end = os.path.basename(files[-1].name).split('.')[0][:7]
        zip_path = os.path.join(folder, f'{begin}-{end}.zip')

        # 写入zip文件
        with zipfile.ZipFile(zip_path, 'w') as myzip:
            for name, pil_img in named_images.items():
                if pil_img is None: continue
                img_bytes = io.BytesIO()
                pil_img.save(img_bytes, format='PNG')  # Write BytesIO object to zip file
                img_bytes.seek(0)                      # Go to the start of the BytesIO object
                myzip.writestr(name, img_bytes.read())
    except Exception as e:
        logger.error(str(e))
    # 临时文件不用保存
    for f in files:
        os.remove(f.name)
    return zip_path

css = """
.preview_origin, .preview_result, .preview_origin img, .preview_result img {height: 70vh !important; }
.preview_result {background: url(https://img2.imgtp.com/2024/05/12/2OuHyE4Q.jpg);}
"""

# 使用 Gradio 设计前端界面，fn 绑定处理函数
with gr.Blocks(css=css, title="在线抠图") as app:
    with gr.Tab(label='在线抠图'):
        with gr.Row(elem_id='restricted-height'):
            origin_image = gr.Image(label='origin', elem_classes='preview_origin', type="pil")
            result_image = gr.Image(label='result', elem_classes='preview_result', image_mode='RGBA')
        with gr.Row():
            select_model = gr.Radio(label="抠图模型", choices=model_options, value=model_options[0])
            gr.Markdown(value=model_hint)
            # retry_btn = gr.Button('回炉重抠')
    origin_image.change(fn=handle_single_image, inputs=[origin_image, select_model], outputs=[result_image])
    select_model.change(fn=handle_single_image, inputs=[origin_image, select_model], outputs=[result_image])

    with gr.Tab(label='批处理'):
        with gr.Row():
            files_in = gr.File(
                label="拖入多个文件", show_label=True, file_count='multiple',
                file_types=['image'], type='filepath', interactive=True
            )
            files_out = gr.File(label='输出', visible=True)
        with gr.Row():
            select_model2 = gr.Radio(label="抠图模型", choices=model_options, value=model_options[0])
            gr.Markdown(value=model_hint)
    files_in.change(fn=handle_multiple_images, inputs=[files_in, select_model2], outputs=[files_out])

    with gr.Tab(label='背景替换'):
        with gr.Row():
            bg_in = gr.Image(label='背景', elem_classes='preview_origin', type="pil")
            fg_in = gr.Image(label='前景', elem_classes='preview_origin', type="pil")
            merged_out = gr.Image(label='结果', elem_classes='preview_origin', image_mode='RGBA')
        with gr.Row():
            select_model3 = gr.Radio(label="抠图模型", choices=model_options, value=model_options[0])
            btn_merge = gr.Button(value="合成")
    btn_merge.click(fn=handle_img_merge, inputs=[bg_in, fg_in, select_model3], outputs=[merged_out])

app.launch(
    server_name="0.0.0.0",
    inbrowser=True,  # 自动打开浏览器
    share=False,
    server_port=8080,
    quiet=True,
    root_path="/aiimg",
    favicon_path="favicon.ico",
)
