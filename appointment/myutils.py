import hashlib


def get_md5_8th(orderpk):
    return hashlib.md5(str(orderpk).encode(encoding='UTF-8')).hexdigest()[:8]
