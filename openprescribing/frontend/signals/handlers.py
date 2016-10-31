from anymail.signals import tracking
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from allauth.account.signals import user_logged_in

from frontend.models import Profile


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(user_logged_in, sender=User)
def handle_user_logged_in(sender, request, user, **kwargs):
    user.searchbookmark_set.update(approved=True)
    user.orgbookmark_set.update(approved=True)


@receiver(tracking)
def handle_open(sender, event, esp_name, **kwargs):
    if event.event_type == 'opened':
        print("Message %s to %s bounced" % (
              event.message_id, event.recipient))


@receiver(tracking)
def handle_click(sender, event, esp_name, **kwargs):
    if event.event_type == 'clicked':
        print("Recipient %s clicked url %s" % (
              event.recipient, event.click_url))


@receiver(tracking)
def handle_deliver(sender, event, esp_name, **kwargs):
    if event.event_type == 'delivered':
        print("Recipient %s clicked url %s" % (
              event.recipient, event.click_url))


@receiver(tracking)
def handle_unsubscribe(sender, event, esp_name, **kwargs):
    if event.event_type == 'unsubscribed':
        print("Recipient %s clicked url %s" % (
              event.recipient, event.click_url))
