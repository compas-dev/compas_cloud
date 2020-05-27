from io import BytesIO
import numpy as np


def encode(nda):
    nda = np.array(nda)
    nda_bytes = BytesIO()
    np.save(nda_bytes, nda, allow_pickle=False)
    return nda_bytes.getvalue()


def decode(nda_bytes):
    nda_bytes = BytesIO(nda_bytes)
    return np.load(nda_bytes, allow_pickle=False)


def encode_args(**args):
    return {key: encode(args[key]) for key in args}

def decode_args(**args):
    return {key: decode(args[key]) for key in args}