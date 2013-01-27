from django.conf.urls.defaults import patterns, url

from torrent.views import TorrentMain, TorrentList

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
)
