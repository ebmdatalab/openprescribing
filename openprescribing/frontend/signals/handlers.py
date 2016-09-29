from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from frontend.models import Profile


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
