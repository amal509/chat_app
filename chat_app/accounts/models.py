from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def last_seen_display(self):
        if self.is_online:
            return 'Online'
        if not self.last_seen:
            return 'Offline'
        now = timezone.now()
        diff = now - self.last_seen
        if diff.total_seconds() < 60:
            return 'Last seen just now'
        local_now = timezone.localtime(now)
        local_last_seen = timezone.localtime(self.last_seen)
        if local_last_seen.date() == local_now.date():
            return f'Last seen today at {local_last_seen.strftime("%H:%M")}'
        if local_last_seen.date() == (local_now - timedelta(days=1)).date():
            return f'Last seen yesterday at {local_last_seen.strftime("%H:%M")}'
        return f'Last seen {local_last_seen.strftime("%d %b %Y")}'