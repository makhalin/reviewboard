import os
import time

from django.core.management.base import BaseCommand
from django.conf import settings

from anytask_sync_extension.models import AnytaskSyncInfo


class Command(BaseCommand):
    help = "Creates missing anytask issue symlinks"

    def handle(self, *args, **options):
        start_time = time.time()

        if not os.path.exists(settings.SYMLINK_DIR_ROOT):
            os.makedirs(settings.SYMLINK_DIR_ROOT)
            os.popen("cp -r {0} {1}".format(settings.SYMLINK_DIR_BASE, settings.SYMLINK_DIR_ROOT))

        num_checks = 0
        num_created = 0
        for name in AnytaskSyncInfo.objects.values_list("name", flat=True):
            repository_path = os.path.join(settings.SYMLINK_DIR, name)
            if not os.path.exists(repository_path):
                os.symlink(settings.SYMLINK_DIR, repository_path)
                num_created += 1
            num_checks += 1

        print "Command create_symlinks checks {0} symlinks (created {1}) and took {2} seconds" \
            .format(num_checks, num_created, time.time() - start_time)
