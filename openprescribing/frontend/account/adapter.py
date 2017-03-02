from allauth.account.adapter import DefaultAccountAdapter
from frontend.models import EmailMessage


class CustomAdapter(DefaultAccountAdapter):
    def add_message(self, *args, **kw):
        """For now, we don't want messages appearing for the end user unless
        we specify them

        """
        pass

    def send_mail(self, template_prefix, email, context):
        """Take a copy of an email before sending it
        """
        msg = self.render_mail(template_prefix, email, context)
        msg.extra_headers = {'message-id': msg.message()['message-id']}
        msg.tags = ['allauth']
        msg = EmailMessage.objects.create_from_message(msg)
        msg.send()
