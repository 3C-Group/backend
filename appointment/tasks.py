import datetime
from .models import *


def expire_by_5min():
    five_mins_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)
    expired_orders = Order.objects.filter(status=Order.Status.UNPAID, created_time__lt=five_mins_ago)
    for order in expired_orders:
        order.status = Order.Status.OUTDATED
        order.save()

def expire_by_notused():
    expired_orders = Order.objects.filter(status=Order.Status.PAID, end_time__lt=datetime.datetime.now())
    for order in expired_orders:
        order.status = Order.Status.OUTDATED
        user = order.user
        user.balance += order.price
        user.save()
        order.save()

