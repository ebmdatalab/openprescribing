import hashlib
import logging

from django.conf import settings
from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError

from common.utils import get_env_setting

logger = logging.getLogger(__name__)


def mailchimp_subscribe(
        request, email, first_name, last_name,
        organisation, job_title):
    """Subscribe `email` to newsletter.

    Returns boolean indicating success
    """
    del(request.session['newsletter_email'])
    email_hash = hashlib.md5(email).hexdigest()
    data = {
        'email_address': email,
        'status': 'subscribed',
        'merge_fields': {
            'FNAME': first_name,
            'LNAME': last_name,
            'MMERGE3': organisation,
            'MMERGE4': job_title
        }
    }
    client = MailChimp(
        mc_user=get_env_setting('MAILCHIMP_USER'),
        mc_api=get_env_setting('MAILCHIMP_API_KEY'))
    try:
        client.lists.members.get(
            list_id=settings.MAILCHIMP_LIST_ID,
            subscriber_hash=email_hash)
        return True
    except MailChimpError:
        try:
            client.lists.members.create(
                list_id=settings.MAILCHIMP_LIST_ID, data=data)
            return True
        except MailChimpError:
            # things like blacklisted emails, etc
            logger.warn("Unable to subscribe %s to newsletter", email)
            return False
