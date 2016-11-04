import logging

from allauth.account.signals import user_logged_in
from anymail.signals import tracking
from requests_futures.sessions import FuturesSession

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from common.utils import google_user_id
from frontend.models import Profile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(user_logged_in, sender=User)
def handle_user_logged_in(sender, request, user, **kwargs):
    user.searchbookmark_set.update(approved=True)
    user.orgbookmark_set.update(approved=True)


def send_ga_event(event):
    user = User.objects.filter(email=event.recipient)
    if user:
        user = user[0]
        session = FuturesSession()
        payload = {
            'v': 1,
            'tid': settings.GOOGLE_TRACKING_ID,
            'cid': google_user_id(user),
            't': 'event',
            'ec': 'email',
            'ea': event.event_type,
            'ua': event.user_agent,
            'cm': 'email',
        }
        if event.esp_event:
            payload['dt'] = event.esp_event['subject']
            payload['cn'] = event.esp_event['campaign_name']
            payload['cs'] = event.esp_event['campaign_source']
            payload['dp'] = "/email/%s/%s/%s/%s" % (
                event.esp_event['campaign_name'],
                event.esp_event['campaign_source'],
                event.esp_event['user_id'],
                event.event_type
            )
        else:
            logger.warn("No esp_event found for event: %s" % event.__dict__)
        logger.info("Sending mail event data Analytics: %s" % payload)
        session.post(
            'https://www.google-analytics.com/collect', data=payload)
    else:
        logger.warn("Could not find receipient %s" % event.recipient)


@receiver(tracking)
def handle_anymail_webhook(sender, event, esp_name, **kwargs):
    logger.debug("Received webhook from %s: %s" % (esp_name))
    send_ga_event(event)
