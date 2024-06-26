import os
from typing import List

import numpy as np
# import pooch
from PIL import Image
from PIL.Image import Image as PILImage
from scipy.special import log_softmax

from .base import BaseSession

palette1 = [
    0,0,0,
    255,255,255,
    0,0,0,
    0,0,0,
]

palette2 = [
    0,0,0,
    0,0,0,
    255,255,255,
    0,0,0,
]

palette3 = [
    0,0,0,
    0,0,0,
    0,0,0,
    255,255,255,
]

palette4 = [
    0,0,0,
    255,255,255,
    255,255,255,
    255,255,255,
]


class Unet2ClothSession(BaseSession):
    def predict(self, img: PILImage, *args, **kwargs) -> List[PILImage]:
        """
        Predict the cloth category of an image.

        This method takes an image as input and predicts the cloth category of the image.
        The method uses the inner_session to make predictions using a pre-trained model.
        The predicted mask is then converted to an image and resized to match the size of the input image.
        Depending on the cloth category specified in the method arguments, the method applies different color palettes to the mask and appends the resulting images to a list.

        Parameters:
            img (PILImage): The input image.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            List[PILImage]: A list of images representing the predicted masks.
        """
        ort_outs = self.inner_session.run(
            None,
            self.normalize(
                img, (0.485, 0.456, 0.406), (0.229, 0.224, 0.225), (768, 768)
            ),
        )

        pred = log_softmax(ort_outs[0], 1)
        pred = np.argmax(pred, axis=1)[0]
        pred[pred < 0.5] = 0

        mask = Image.fromarray(pred.astype("uint8"), mode="L")
        mask = mask.resize(img.size, Image.LANCZOS)

        masks = []

        cloth_category = kwargs.get("cc") or kwargs.get("cloth_category")

        def upper_cloth():
            mask1 = mask.copy()
            mask1.putpalette(palette1)
            masks.append(mask1.convert("RGB").convert("L"))

        def lower_cloth():
            mask2 = mask.copy()
            mask2.putpalette(palette2)
            masks.append(mask2.convert("RGB").convert("L"))

        def full_cloth():
            mask3 = mask.copy()
            mask3.putpalette(palette3)
            masks.append(mask3.convert("RGB").convert("L"))

        def all_cloth():
            m = mask.copy()
            m.putpalette(palette4)
            masks.append(m.convert("RGB").convert("L"))

        if cloth_category == "upper":
            upper_cloth()
        elif cloth_category == "lower":
            lower_cloth()
        elif cloth_category == "full":
            full_cloth()
        else:
            all_cloth()

        return masks

    @classmethod
    def download_models(cls, *args, **kwargs):
        fname = f"{cls.name(*args, **kwargs)}.onnx"
        # pooch.retrieve(
        #     "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_cloth_seg.onnx",
        #     (
        #         None
        #         if cls.checksum_disabled(*args, **kwargs)
        #         else "md5:2434d1f3cb744e0e49386c906e5a08bb"
        #     ),
        #     fname=fname,
        #     path=cls.u2net_home(*args, **kwargs),
        #     progressbar=True,
        # )
        # return os.path.join(cls.u2net_home(*args, **kwargs), fname)
        return f"{cls.model_base_dir}/{fname}"

    @classmethod
    def name(cls, *args, **kwargs):
        return "u2net_cloth_seg"
