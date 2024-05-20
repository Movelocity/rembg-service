from __future__ import annotations

import os

from typing import List, Type
import onnxruntime as ort

from .base import BaseSession
sessions_class: List[type[BaseSession]] = []
sessions_names: List[str] = []

# 为每个抠图模型注册 session
from .dis_anime import DisSession
sessions_class.append(DisSession)
sessions_names.append(DisSession.name())

from .dis_general_use import DisSession as DisSessionGeneralUse
sessions_class.append(DisSessionGeneralUse)
sessions_names.append(DisSessionGeneralUse.name())

from .sam import SamSession
sessions_class.append(SamSession)
sessions_names.append(SamSession.name())

from .rmbg14 import RMBG14Session
sessions_class.append(RMBG14Session)
sessions_names.append(RMBG14Session.name())

from .silueta import SiluetaSession

sessions_class.append(SiluetaSession)
sessions_names.append(SiluetaSession.name())

from .u2net_cloth_seg import Unet2ClothSession
sessions_class.append(Unet2ClothSession)
sessions_names.append(Unet2ClothSession.name())

from .u2net_custom import U2netCustomSession
sessions_class.append(U2netCustomSession)
sessions_names.append(U2netCustomSession.name())

from .u2net_human_seg import U2netHumanSegSession
sessions_class.append(U2netHumanSegSession)
sessions_names.append(U2netHumanSegSession.name())

from .u2net import U2netSession
sessions_class.append(U2netSession)
sessions_names.append(U2netSession.name())

from .u2netp import U2netpSession
sessions_class.append(U2netpSession)
sessions_names.append(U2netpSession.name())


def new_session(
    model_name: str = "u2net", providers=None, *args, **kwargs
) -> BaseSession:
    """
    Create a new session object based on the specified model name.

    This function searches for the session class based on the model name in the 'sessions_class' list.
    It then creates an instance of the session class with the provided arguments.
    The 'sess_opts' object is created using the 'ort.SessionOptions()' constructor.
    If the 'OMP_NUM_THREADS' environment variable is set, the 'inter_op_num_threads' option of 'sess_opts' is set to its value.

    Parameters:
        model_name (str): The name of the model.
        providers: The providers for the session.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

    Returns:
        BaseSession: The created session object.
    """
    session_class: Type[BaseSession] = U2netSession

    for sc in sessions_class:
        if sc.name() == model_name:
            session_class = sc
            break

    sess_opts = ort.SessionOptions()

    if "OMP_NUM_THREADS" in os.environ:
        sess_opts.inter_op_num_threads = int(os.environ["OMP_NUM_THREADS"])
        sess_opts.intra_op_num_threads = int(os.environ["OMP_NUM_THREADS"])

    return session_class(model_name, sess_opts, providers, *args, **kwargs)