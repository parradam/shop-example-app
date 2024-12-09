from celery import shared_task
from django.core.mail import send_mail
from .models import Order

@shared_task
def order_created(order_id):
    """
    Tasks to send an email notification when an order is
    created.
    """

    order = Order.objects.get(id=order_id)
    subject = f'Order number: {order.id}'
    message = (
        f'Dear {order.first_name}\n\n'
        f'Your order has been placed.'
        f'Your order ID is {order.id}'
    )
    mail_sent = send_mail(
        subject, message, 'admin@myshop.com', [order.email]
    )
    return mail_sent