import json
import hashlib
from .models import *


def get_all_notice():
    notice_set = Notice.objects.order_by('-time')
    retdata = [notice.get_dict() for notice in notice_set]
    return json.dumps(retdata, ensure_ascii=False)


def create_notice(title, content, author, timetext, file):
    time = datetime.datetime.strptime(timetext, TIME_FORMAT)
    noticepk = Notice.objects.create_notice(title, content, author, time)
    if file:
        notice = Notice.objects.get(pk=noticepk)
        notice.file = file
        notice.filename = file.name
        notice.save()
    return noticepk


def modify_notice(noticepk, title, content, author, timetext, file):
    notice = Notice.objects.get(pk=int(noticepk))
    if timetext:
        time = datetime.datetime.strptime(timetext, TIME_FORMAT)
        notice.time = time
    if title:
        notice.title = title
    if content:
        notice.content = content
    if author:
        notice.author = author
    if file:
        notice.file = file
        notice.filename = file.name
    notice.save()
    return "success"


def delete_notice(noticepk):
    notice = Notice.objects.get(pk=int(noticepk))
    notice.delete()
    return "success"
