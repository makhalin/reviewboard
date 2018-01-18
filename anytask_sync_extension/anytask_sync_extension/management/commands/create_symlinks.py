import os

from django.core.management.base import BaseCommand
from django.conf import settings

from anytask_sync_extension.models import AnytaskSyncInfo


class Command(BaseCommand):
    help = "Creates missing anytask issue symlinks"

    def handle(self, *args, **options):
        for name in AnytaskSyncInfo.objects.values_list("name", flat=True):
            repository_path = os.path.join(settings.SYMLINK_DIR, name)
            if not os.path.exists(repository_path):
                os.symlink(settings.SYMLINK_DIR, repository_path)
