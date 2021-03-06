from __future__ import unicode_literals

import json
import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from djblets.cache.forwarding_backend import DEFAULT_FORWARD_CACHE_ALIAS
from djblets.siteconfig.models import SiteConfiguration
from djblets.siteconfig.views import site_settings as djblets_site_settings

from reviewboard.accounts.models import Profile
from reviewboard.admin.cache_stats import get_cache_stats
from reviewboard.admin.forms import SSHSettingsForm
from reviewboard.admin.security_checks import SecurityCheckRunner
from reviewboard.admin.support import get_support_url, serialize_support_data
from reviewboard.admin.widgets import (dynamic_activity_data,
                                       primary_widgets,
                                       secondary_widgets)
from reviewboard.ssh.client import SSHClient
from reviewboard.ssh.utils import humanize_key


@staff_member_required
def dashboard(request, template_name="admin/dashboard.html"):
    """Display the administration dashboard.

    This is the entry point to the admin site, containing news updates and
    useful administration tasks.
    """
    profile = Profile.objects.get_or_create(user=request.user)[0]

    if profile.extra_data is None:
        profile.extra_data = {}
        profile.save(update_fields=('extra_data',))

    profile_data = profile.extra_data

    selected_primary_widgets = []
    unselected_primary_widgets = []
    primary_widget_selections = profile_data.get('primary_widget_selections')
    if primary_widget_selections:
        for p in primary_widgets:
            if primary_widget_selections[p.widget_id] == "1":
                selected_primary_widgets.append(p)
            else:
                unselected_primary_widgets.append(p)
    else:
        selected_primary_widgets = primary_widgets
        unselected_primary_widgets = None

    selected_secondary_widgets = []
    unselected_secondary_widgets = []
    secondary_widget_selections = profile_data.get(
        'secondary_widget_selections')
    if secondary_widget_selections:
        for s in secondary_widgets:
            if secondary_widget_selections[s.widget_id] == "1":
                selected_secondary_widgets.append(s)
            else:
                unselected_secondary_widgets.append(s)
    else:
        selected_secondary_widgets = secondary_widgets
        unselected_secondary_widgets = None

    primary_widget_positions = profile_data.get('primary_widget_positions')
    if primary_widget_positions:
        sorted_primary_widgets = sorted(
            selected_primary_widgets,
            key=(lambda y: primary_widget_positions[y.widget_id] or
                 len(primary_widget_positions)))
    else:
        sorted_primary_widgets = selected_primary_widgets

    secondary_widget_positions = profile_data.get('secondary_widget_positions')
    if secondary_widget_positions:
        sorted_secondary_widgets = sorted(
            selected_secondary_widgets,
            key=(lambda y: secondary_widget_positions[y.widget_id] or
                 len(secondary_widget_positions)))
    else:
        sorted_secondary_widgets = selected_secondary_widgets

    return render_to_response(template_name, RequestContext(request, {
        'primary_widgets': primary_widgets,
        'root_path': settings.SITE_ROOT + 'admin/db/',
        'secondary_widgets': secondary_widgets,
        'selected_primary_widgets': sorted_primary_widgets,
        'selected_secondary_widgets': sorted_secondary_widgets,
        'support_data': serialize_support_data(request, True),
        'title': _("Admin Dashboard"),
        'unselected_primary_widgets': unselected_primary_widgets,
        'unselected_secondary_widgets': unselected_secondary_widgets,
    }))


@staff_member_required
def cache_stats(request, template_name="admin/cache_stats.html"):
    """Display statistics on the cache.

    This includes such pieces of information as memory used, cache misses, and
    uptime.
    """
    cache_stats = get_cache_stats()
    cache_info = settings.CACHES[DEFAULT_FORWARD_CACHE_ALIAS]

    return render_to_response(template_name, RequestContext(request, {
        'cache_hosts': cache_stats,
        'cache_backend': cache_info['BACKEND'],
        'title': _("Server Cache"),
        'root_path': settings.SITE_ROOT + "admin/db/"
    }))


@staff_member_required
def security(request, template_name="admin/security.html"):
    """Run security checks and report the results."""
    runner = SecurityCheckRunner()
    results = runner.run()
    return render_to_response(template_name, RequestContext(request, {
        'test_results': results,
        'title': _("Security Checklist"),
    }))


@csrf_protect
@staff_member_required
def site_settings(request, form_class,
                  template_name="siteconfig/settings.html"):
    """Render the general site settings page."""
    return djblets_site_settings(request, form_class, template_name, {
        'root_path': settings.SITE_ROOT + "admin/db/"
    })


@csrf_protect
@staff_member_required
def ssh_settings(request, template_name='admin/ssh_settings.html'):
    """Render the SSH settings page."""
    client = SSHClient()
    key = client.get_user_key()

    if request.method == 'POST':
        form = SSHSettingsForm(request.POST, request.FILES)

        if form.is_valid():
            if form.did_request_delete() and client.get_user_key() is not None:
                try:
                    form.delete()
                    return HttpResponseRedirect('.')
                except Exception as e:
                    logging.error('Deleting SSH key failed: %s' % e)
            else:
                try:
                    form.create(request.FILES)
                    return HttpResponseRedirect('.')
                except Exception as e:
                    # Fall through. It will be reported inline and in the log.
                    logging.error('Uploading SSH key failed: %s' % e)
    else:
        form = SSHSettingsForm()

    if key:
        fingerprint = humanize_key(key)
    else:
        fingerprint = None

    return render_to_response(template_name, RequestContext(request, {
        'key': key,
        'fingerprint': fingerprint,
        'public_key': client.get_public_key(key),
        'form': form,
    }))


def manual_updates_required(
        request, updates,
        template_name="admin/manual_updates_required.html"):
    """Render the "manual updates required" page."""
    return render_to_response(template_name, RequestContext(request, {
        'updates': [render_to_string(update_template_name,
                                     RequestContext(request, extra_context))
                    for (update_template_name, extra_context) in updates],
    }))


def widget_toggle(request):
    """Toggle a widget's collapsed state.

    This will update the saved state of the admin widgets based on a user's
    activity in the dashboard.
    """
    collapsed = request.GET.get('collapse', None)
    widget = request.GET.get('widget', None)

    if widget and collapsed:
        siteconfig = SiteConfiguration.objects.get_current()
        widget_settings = siteconfig.get("widget_settings", {})

        widget_settings[widget] = collapsed
        siteconfig.set("widget_settings", widget_settings)
        siteconfig.save()

    return HttpResponse("")


def widget_move(request):
    """Handle moving of admin widgets.

    This will update the saved position of the admin widgets based on a user's
    activity in the dashboard.
    """
    profile = Profile.objects.get_or_create(user=request.user)[0]
    profile_data = profile.extra_data

    widget_type = request.POST.get('type')

    if widget_type == 'primary':
        positions_key = 'primary_widget_positions'
        widgets = primary_widgets
    else:
        positions_key = 'secondary_widget_positions'
        widgets = secondary_widgets

    positions = profile_data.setdefault(positions_key, {})

    for widget in widgets:
        widget_position = request.POST.get(widget.widget_id)
        if widget_position is not None:
            positions[widget.widget_id] = widget_position
        else:
            # All widgets removed from the dashboard have the same position.
            positions[widget.widget_id] = str(len(widgets))

    profile.save()

    return HttpResponse()


def widget_select(request):
    """Handle selection of admin widgets.

    This will enable or disable widgets based on a user's activity in the
    dashboard.
    """
    profile = Profile.objects.get_or_create(user=request.user)[0]
    profile_data = profile.extra_data

    widget_type = request.POST.get('type')

    if widget_type == 'primary':
        selections_key = 'primary_widget_selections'
        widgets = primary_widgets
    else:
        selections_key = 'secondary_widget_selections'
        widgets = secondary_widgets

    initial_selections = {}
    for widget in widgets:
        initial_selections[widget.widget_id] = "1"

    selections = profile_data.setdefault(selections_key, initial_selections)

    for widget in widgets:
        widget_selection = request.POST.get(widget.widget_id)
        if widget_selection is not None:
            selections[widget.widget_id] = widget_selection

    profile.save()

    return HttpResponse()


def widget_activity(request):
    """Return JSON data for the admin activity widget."""
    activity_data = dynamic_activity_data(request)

    return HttpResponse(json.dumps(activity_data),
                        content_type="application/json")


def support_redirect(request, **kwargs):
    """Return an HttpResponseRedirect to the Beanbag support page."""
    return HttpResponseRedirect(get_support_url(request))
