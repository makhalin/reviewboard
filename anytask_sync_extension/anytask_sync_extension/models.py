from django.db import models


class AnytaskSyncInfo(models.Model):
    name = models.CharField(max_length=128, unique=True, blank=False, null=False)
