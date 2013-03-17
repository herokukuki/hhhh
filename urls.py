from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from torrent.views import TorrentList, TorrentAction

urlpatterns = patterns(
    'torrent.views',
    url(r'^$',
        view=login_required(
            TemplateView.as_view(template_name="torrent/torrent.html")),
        name='torrent',
    ),
    url(r'^torrents$',
        view=login_required(TorrentList.as_view()),
        name='torrent_torrent_list',
    ),
    url(r'^action(?:/(?P<id>[0-9]+))?/(?P<action>start|stop|add)'
        '(?:/(?P<hash>[0-9a-f]{40}))?$',
        view=login_required(TorrentAction.as_view()),
        name='torrent_torrent_action',
    ),
)
