from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from torrent.views import TorrentList, TorrentAction, TorrentDetail, TorrentView

urlpatterns = [
    url(r'^$',
        view=login_required(TorrentView.as_view()),
        name='torrent',
    ),
    url(r'^(?P<id>[0-9]+)$',
        view=login_required(TorrentDetail.as_view()),
        name='torrent_torrent_detail',
    ),
    url(r'^torrents(?:/(?P<format>json))?$',
        view=login_required(TorrentList.as_view()),
        name='torrent_torrent_list',
    ),
    url(r'^action(?:/(?P<id>[0-9]+))?/(?P<action>start|stop|add|remove)'
        '(?:/(?P<hash>[0-9a-f]{40}))?$',
        view=login_required(TorrentAction.as_view()),
        name='torrent_torrent_action',
    ),
]
