# rembg-service
uses multiple opensource models to remove background of image, share with gradio


## 项目启动方式
```shell
git clone https://github.com/Movelocity/rembg-service.git
pip install -r requirements.txt

mkdir model_weights # 往这个路径里放模型权重文件，huggingface格式的模型则以文件夹为单位。主要的一些模型权重都是在rembg开源项目获取的。

python webui.py
```

如果无法启动，可能是 python 版本过低，使用以下方法修复两个库
```shell
pip uninstall fastapi
pip uninstall pydantic
pip install fastapi==0.99.1 -i https://repo.huaweicloud.com/repository/pypi/simple
pip install pydantic==1.10.11 -i https://repo.huaweicloud.com/repository/pypi/simple
```

note 
- requires python>=3.9, python 3.7 对应的最高版本 gradio 存在图片重复上传的 bug

## 增加模型的流程

1. 在 sessions 目录下添加模型对应的 .py 文件，建立模型类，继承 BaseSession，重载三个函数
```python
from .base import BaseSession
class MyModel(BaseSession):
    def __init__(self, model_name: str,*args,**kwargs):
        self.model_name = model_name
        # model_name为 模型索引名，用于根据字符串找到模型
        # ... 自行加载模型

    def predict(self, img: PILImage, *args, **kwargs) -> List[PILImage]:
        # 输入图片，返回相同尺寸的单通道 mask。为了统一各个模型接口，返回类型定义为 list[mask], 如果只返回一张 mask，可以仅在列表内放一个 mask
    
    @classmethod
    def name(cls, *args, **kwargs):
        # 重载此函数，返回模型索引名
        return "mymodel123"
```
2. 在 sessions/__init__.py 注册新加的模型类
```python
from .mymodel import MyModel
sessions_class.append(MyModel)
sessions_names.append(MyModel.name())
```
3. 通过 session 查找和加载模型
```python
from sessions import new_session
mymodel = new_session(model_name="mymodel123")
```
4. 使用模型预测蒙版
```python
from PIL import Image
img = Image.open('xxx')
mask = mymodel.predict(img)
mask.show()
```


开发进度

- [x] 所有 onnx 模型的单样本推理
- [x] Gradio 前端界面生成，布局调整
- [x] 模型选择
- [x] 加入 rmbg-1.4 模型
- [x] GPU 单样本推理
- [x] 多文件上传，zip 文件下载
- [x] 预测结果从内存直接写入 zip 文件，省去写入磁盘的时间
