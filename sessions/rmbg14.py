import os
from typing import List, Tuple, Dict

import numpy as np
from PIL import Image
from PIL.Image import Image as PILImage
from .base import BaseSession

import torch
from transformers import AutoModelForImageSegmentation

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# device = torch.device('cpu')

class RMBG14Session(BaseSession):
    """This is a class representing a SiluetaSession object."""
    def __init__(
        self,
        model_name: str,
        sess_opts: None,
        providers=None,
        *args,
        **kwargs
    ):
        """Initialize an instance of the BaseSession class."""
        self.model_name = model_name
        self.providers = []
        self.model = AutoModelForImageSegmentation.from_pretrained("model_weights/rmbg14", trust_remote_code=True).eval().to(device)
    
    def predict(self, img: PILImage, *args, **kwargs) -> List[PILImage]:
        """
        Predict the mask of the input image.

        This method takes an image as input, preprocesses it, and performs a prediction to generate a mask. 
        The generated mask is then post-processed and returned as a list of PILImage objects.

        Parameters:
            img (PILImage): The input image to be processed.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            List[PILImage]: A list of post-processed masks.
        """
        normed_img = self.normalize(img, (0.5,0.5,0.5), (1.0, 1.0, 1.0), (768, 768)) # 可以上 1024x1024

        with torch.no_grad():
            masks_pt = self.model(torch.tensor(normed_img, device=device))
        
        masks = []
        for i in range(2):
            for j in range(2):
                mask = masks_pt[i][j][0, 0].cpu().numpy()
                ma, mi = np.max(mask), np.min(mask)
                mask = (mask - mi) / (ma - mi)
                mask = Image.fromarray((mask * 255).astype("uint8"), mode="L")
                mask = mask.resize(img.size, Image.LANCZOS)
                masks.append(mask)
        return masks

    def normalize(
        self,
        img: PILImage,
        mean: Tuple[float, float, float],
        std: Tuple[float, float, float],
        size: Tuple[int, int],
        *args,
        **kwargs
    ) -> np.ndarray:
        im = img.convert("RGB").resize(size, Image.LANCZOS)

        im_ary = np.array(im)
        im_ary = im_ary / np.max(im_ary)

        tmpImg = np.zeros((im_ary.shape[0], im_ary.shape[1], 3))
        tmpImg[:, :, 0] = (im_ary[:, :, 0] - mean[0]) / std[0]
        tmpImg[:, :, 1] = (im_ary[:, :, 1] - mean[1]) / std[1]
        tmpImg[:, :, 2] = (im_ary[:, :, 2] - mean[2]) / std[2]

        tmpImg = tmpImg.transpose((2, 0, 1))

        return np.expand_dims(tmpImg, 0).astype(np.float32)

    @classmethod
    def download_models(cls, *args, **kwargs):
        return ""

    @classmethod
    def name(cls, *args, **kwargs):
        """
        模型的索引命名

        Parameters:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The name of the model.
        """
        return "rmbg14"