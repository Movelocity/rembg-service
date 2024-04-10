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

def batch_list(input_list, batch_size=16):
    # Create batches of 16 samples each
    return [input_list[i:i + batch_size] for i in range(0, len(input_list), batch_size)]

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
    
    # def predict(self, img: PILImage, *args, **kwargs) -> List[PILImage]:
    #     """
    #     Predict the mask of the input image.
    #     Parameters:
    #         img (PILImage): The input image to be processed.
    #         *args: Variable length argument list.
    #         **kwargs: Arbitrary keyword arguments.
    #     Returns:
    #         List[PILImage]: A list of post-processed masks.
    #     """
    #     normed_img = self.normalize(img, (0.5,0.5,0.5), (1.0, 1.0, 1.0), (768, 768)) # 可以上 1024x1024

    #     with torch.no_grad():
    #         masks_pt = self.model(torch.tensor(normed_img, device=device))
        
    #     masks = []
    #     for i in range(2):
    #         for j in range(2):
    #             mask = masks_pt[i][j][0, 0].cpu().numpy()
    #             ma, mi = np.max(mask), np.min(mask)
    #             mask = (mask - mi) / (ma - mi)
    #             mask = Image.fromarray((mask * 255).astype("uint8"), mode="L")
    #             mask = mask.resize(img.size, Image.LANCZOS)
    #             masks.append(mask)
    #     return masks

    def predict(self, img: PILImage, *args, **kwargs) -> List[PILImage]:
        """简化版, 只需要第一张 mask"""
        normed_img = self.normalize(img, (0.5,0.5,0.5), (1.0, 1.0, 1.0), (768, 768)) # 可以上 1024x1024

        with torch.no_grad():
            masks_pt = self.model(torch.tensor(normed_img, device=device))
        
        masks = []
        mask = masks_pt[0][0][0, 0].cpu().numpy()
        ma, mi = np.max(mask), np.min(mask)
        mask = (mask - mi) / (ma - mi)
        mask = Image.fromarray((mask * 255).astype("uint8"), mode="L")
        mask = mask.resize(img.size, Image.LANCZOS)
        masks.append(mask)
        return masks
    
    def predict_batch(self, imgs: List[PILImage], *args, **kwargs) -> List[List[PILImage]]:
        """简化版"""
        batch_size = 16
        batches = batch_list(imgs, batch_size)  # tiny batches
        results = []
        for batch in batches:
            normed_batch = self.normalize_batch(batch)
            normed_batch = torch.tensor(normed_batch, device=device)
            with torch.no_grad():
                masks = self.model(normed_batch)[0][0].squeeze(1).cpu().numpy() # (batch, h, w)
            ma, mi = np.max(masks), np.min(masks)
            masks = (masks - mi) / (ma - mi)
            for i in range(masks.shape[0]):
                mask = Image.fromarray((masks[i] * 255).astype("uint8"), mode="L")
                results.append(mask)
        for i, mask in enumerate(results):
            results[i] = mask.resize(imgs[i].size, Image.LANCZOS)
        return results

    def normalize(
        self,
        img: PILImage,
        mean: Tuple[float, float, float] = (0.5,0.5,0.5),
        std: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        size: Tuple[int, int] = (768, 768),
        *args,
        **kwargs
    ) -> np.ndarray:
        im = img.convert("RGB").resize(size, Image.LANCZOS)
        im_ary = np.array(im)
        im_ary = im_ary / im_ary.max()
        tmpImg = np.zeros(im_ary.shape)
        tmpImg[:, :, 0] = (im_ary[:, :, 0] - mean[0]) / std[0]
        tmpImg[:, :, 1] = (im_ary[:, :, 1] - mean[1]) / std[1]
        tmpImg[:, :, 2] = (im_ary[:, :, 2] - mean[2]) / std[2]
        tmpImg = tmpImg.transpose((2, 0, 1))
        return np.expand_dims(tmpImg, 0).astype(np.float32)

    def normalize_batch(
        self,
        imgs: List[PILImage],
        mean: Tuple[float, float, float] = (0.5,0.5,0.5),
        std: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        size: Tuple[int, int] = (768, 768),
        *args,
        **kwargs
    ) -> np.ndarray:
        rbgs = [img.convert("RGB").resize(size, Image.LANCZOS) for img in imgs]
        rbgs_array = np.array(rbgs)
        rbgs_array = rbgs_array / rbgs_array.max()
        tmpImgs = np.zeros(rbgs_array.shape)
        tmpImgs[:, :, :, 0] = (rbgs_array[:, :, :, 0] - mean[0]) / std[0]
        tmpImgs[:, :, :, 1] = (rbgs_array[:, :, :, 1] - mean[1]) / std[1]
        tmpImgs[:, :, :, 2] = (rbgs_array[:, :, :, 2] - mean[2]) / std[2]
        tmpImgs = tmpImgs.transpose((0, 3, 1, 2))
        return tmpImgs.astype(np.float32)

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