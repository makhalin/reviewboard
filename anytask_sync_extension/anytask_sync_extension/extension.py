# description=extension uses to sync review_request with anytask Extension for Review Board.

from __future__ import unicode_literals

import urlparse
import requests

from django.conf import settings
from django.conf.urls import patterns, include
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import reply_published
from reviewboard.reviews.signals import review_published

class AnytaskSyncExtension(Extension):
    metadata = {
        'Name': 'anytask_sync_extension',
        'Summary': 'listen to reply_published signal and send update of review_request to anytask',
    }

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
        url = urlparse.urljoin(settings.ANYTASK_HOST, '/anyrb/update/') + str(review_id)
        req = requests.post(url, data=values)
        #data = urllib.urlencode(values)
        #req = urllib2.Request(url, data)
        #rsp = urllib2.urlopen(req)
        
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
        url = urlparse.urljoin(settings.ANYTASK_HOST, '/anyrb/update/') + str(review_id)
        req = requests.post(url, data=values)
        #data = urllib.urlencode(values)
        #req = urllib2.Request(url, data)
        #rsp = urllib2.urlopen(req)
 