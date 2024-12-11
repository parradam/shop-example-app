from io import BytesIO
import weasyprint
from celery import shared_task
from django.contrib.staticfiles import finders
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from orders.models import Order

@shared_task
def payment_completed(order_id):
    """
    Task to send an email notification when an order is
    successfully paid.
    """

    order = Order.objects.get(id=order_id)

    # Create email
    subject = f'My shop - invoice #{order.id}'
    message = 'Please find attached the invoice for your purchase.'
    email = EmailMessage(
        subject, message, 'admin@myshop.com', [order.email]
    )

    # Generate PDF
    html = render_to_string('orders/order/pdf.html', {'order': order})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(finders.find('css/pdf.css'))]
    weasyprint.HTML(string=html).write_pdf(out, stylesheets=stylesheets)

    # Attach PDF
    email.attach(
        f'order_{order.id}.pdf', out.getvalue(), 'application/pdf'
    )

    # Send email
    email.send()