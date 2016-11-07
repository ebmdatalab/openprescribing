import logging

from allauth.account.signals import user_logged_in
from anymail.signals import tracking
from requests_futures.sessions import FuturesSession

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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


def send_ga_event(event, user):
    session = FuturesSession()
    payload = {
        'v': 1,
        'tid': settings.GOOGLE_TRACKING_ID,
        'uid': google_user_id(user),
        't': 'event',
        'ec': 'email',
        'ea': event.event_type,
        'cm': 'email',
    }
    if event.esp_event:
        payload['ua'] = event.esp_event.get('user-agent')
        payload['dt'] = event.esp_event.get('subject', [None])[0]
        payload['cn'] = event.esp_event.get('campaign_name', None)
        payload['cs'] = event.esp_event.get('campaign_source', None)
        payload['cc'] = payload['el'] = event.esp_event.get(
            'email_id', None)
        payload['dp'] = "%s/%s" % (
            payload['cc'], event.event_type)
    else:
        logger.warn("No ESP event found for event: %s" % event.__dict__)
    logger.info("Sending mail event data Analytics: %s" % payload)
    session.post(
        'https://www.google-analytics.com/collect', data=payload)


@receiver(tracking)
def handle_anymail_webhook(sender, event, esp_name, **kwargs):
    if event.tags and 'monthly_update' in event.tags:
        user = get_user_by_email(event.recipient)
        logger.debug("Handling webhook from %s: %s" % (
            esp_name, event.__dict__))
        send_ga_event(event, user)
        if user:
            if event.event_type == 'delivered':
                user.profile.emails_received += 1
                user.profile.save()
            elif event.event_type == 'opened':
                user.profile.emails_opened += 1
                user.profile.save()
            elif event.event_type == 'clicked':
                user.profile.emails_clicked += 1
                user.profile.save()
    else:
        logger.debug("Received unhandled webhook from %s: %s" % (
            esp_name, event.__dict__))


def get_user_by_email(email):
    user = User.objects.filter(email=email)
    user = user and user[0]
    if not user:
        logger.warn("Could not find recipient %s" % email)
    return user or None
