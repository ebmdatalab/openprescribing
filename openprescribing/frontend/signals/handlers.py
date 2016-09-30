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
