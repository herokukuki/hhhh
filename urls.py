from django.conf.urls.defaults import patterns, url

from torrent.views import TorrentMain, TorrentList, TorrentAction

urlpatterns = patterns(
    'torrent.views',
    url(r'^$',
        view=TorrentMain.as_view(),
        name='torrent',
    ),
    url(r'^torrents$',
        view=TorrentList.as_view(),
        name='torrent_torrent_list',
    ),
    url(r'^action(?:/(?P<id>[0-9]+))?/(?P<action>start|stop|add)'
        '(?:/(?P<hash>[0-9a-f]{40}))?$',
        view=TorrentAction.as_view(),
        name='torrent_torrent_action',
    ),
)
