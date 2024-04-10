# rembg-service
uses multiple opensource models to remove background of image, share with gradio


```
git clone https://github.com/Movelocity/rembg-service.git
pip install -r packages.txt

mkdir model_weights # 往这个路径里放模型参数文件，huggingface格式的模型则以文件夹为单位

python webui.py
```


note 
- requires python>=3.9, python 3.7 对应的最高版本 gradio 存在图片重复上传的 bug


开发进度

- [x] 所有 onnx 模型的单样本推理
- [x] Gradio 前端界面生成，布局调整
- [x] 模型选择
- [x] 加入 rmbg-1.4 模型
- [x] GPU 单样本推理
- [x] 多文件上传，zip 文件下载
- [ ] 预测结果从内存直接写入 zip 文件，省去写入磁盘的时间
