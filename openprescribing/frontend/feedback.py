from email.utils import formataddr

from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import get_template


def send_feedback_mail(user_name, user_email_addr, subject, message, url):
    connection = get_connection()

    ctx = {
        'name': user_name,
        'email_addr': user_email_addr,
        'url': url,
        'message': message,
    }

    template = get_template('feedback_email_to_us.txt')
    body = template.render(ctx)

    email = EmailMultiAlternatives(
        subject='OpenPrescribing Feedback: {}'.format(subject),
        body=body,
        from_email=formataddr((user_name, settings.SUPPORT_FROM_EMAIL)),
        to=[settings.SUPPORT_TO_EMAIL],
        reply_to=[user_email_addr],
        headers={'X-Mailgun-Track': 'no'},
        connection=connection
    )

    email.send()

    ctx = {
        'name': user_name,
        'message': message,
    }

    template = get_template('feedback_email_to_them.txt')
    body = template.render(ctx)

    email = EmailMultiAlternatives(
        subject='OpenPrescribing Feedback: {}'.format(subject),
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email_addr],
        headers={'X-Mailgun-Track': 'no'},
        connection=connection
    )

    email.send()
