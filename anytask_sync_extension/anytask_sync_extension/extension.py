# description=extension uses to sync review_request with anytask Extension for Review Board.

from __future__ import unicode_literals

import urlparse
import requests
import os

from django.conf import settings
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import reply_published
from reviewboard.reviews.signals import review_published
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import WebAPIResource
from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_response_errors,
                                       webapi_request_fields)
from djblets.webapi.errors import DOES_NOT_EXIST, PERMISSION_DENIED

from anytask_sync_extension.models import AnytaskSyncInfo


class SampleExtensionResource(WebAPIResource):
    """Resource for creating reviews"""
    name = 'repo_create'
    uri_name = 'repo'
    allowed_methods = ('POST',)

    def has_access_permissions(self, request, *args, **kwargs):
        return request.user.username == settings.ANYTASK_ADMIN_USERNAME

    @webapi_check_local_site
    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'issue_id': {
                'type': str,
                'description': 'The ID of issue',
            },
        },
    )
    def create(self, request, issue_id, *args, **kwargs):
        if not self.has_access_permissions(request):
            return PERMISSION_DENIED

        AnytaskSyncInfo.objects.get_or_create(name=issue_id)

        repository_path = os.path.join(settings.SYMLINK_DIR, issue_id)
        response = {
            'path': repository_path
        }
        if not os.path.exists(repository_path):
            os.symlink(settings.SYMLINK_DIR, repository_path)
            return 201, response
        return 200, response


sample_review_resource = SampleExtensionResource()


class AnytaskSyncExtension(Extension):
    metadata = {
        'Name': 'anytask_sync_extension',
        'Summary': 'listen to reply_published signal and send update of review_request to anytask',
    }
    resources = [sample_review_resource]

    def initialize(self):
        SignalHook(self, reply_published, self.on_published_replay)
        SignalHook(self, review_published, self.on_published_review)

    def on_published_replay(self, *args, **kwargs):
        reply = kwargs['reply']
        review_id = reply.review_request.get_display_id()
        values = {comment.comment_type: (comment.text).encode('utf-8') for comment in reply.get_all_comments()}
        values['body_top'] = reply.body_top.encode('utf-8')
        values['body_bottom'] = reply.body_bottom.encode('utf-8')
        values['author'] = reply.user.username

        requests.post(
            urlparse.urljoin(settings.ANYTASK_HOST, '/anyrb/update/') + str(review_id),
            data=values,
            headers={'OAUTH': settings.RB_API_OAUTH},
            verify=False
        )

    def on_published_review(self, *args, **kwargs):
        review = kwargs['review']
        review_id = review.review_request.get_display_id()
        values = {comment.comment_type: (comment.text).encode('utf-8') for comment in review.get_all_comments()}
        values['body_top'] = review.body_top.encode('utf-8')
        values['body_bottom'] = review.body_bottom.encode('utf-8')
        values['author'] = review.user.username
        for comment in review.get_all_comments():
            if comment.comment_type == 'diff':
                values['diff-url'] = comment.get_absolute_url()

        requests.post(
            urlparse.urljoin(settings.ANYTASK_HOST, '/anyrb/update/') + str(review_id),
            data=values,
            headers={'OAUTH': settings.RB_API_OAUTH},
            verify=False
        )
