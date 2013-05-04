from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.views.generic import View, ListView

from torrent.models import Torrent

_DEFAULT_DIR = '/home/media/downloads/'
_DEFAULT_DIRS = {
    'music': '/home/media/mlib',
    'movie': '/home/media/mov/Movies',
    'tv': '/home/media/mov/TV',
}
TORRENT_DIRS = getattr(settings, 'TORRENT_DIRS', _DEFAULT_DIRS)


class TorrentList(ListView):
    def get_queryset(self):
        if self.request.user.is_superuser:
            Torrent.objects.sync()
            return Torrent.objects.active()
        return Torrent.objects.none()


class TorrentAction(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponse("You don't have the permissions to do that!")
        if kwargs['action'] in ['stop', 'start', 'remove']:
            try:
                torrent = Torrent.objects.get(base_id=kwargs['id'])
            except Torrent.DoesNotExist as e:
                raise Http404()

        if kwargs['action'] == 'stop':
            result = Torrent.objects.client.stop_torrent(torrent.base_id)
        elif kwargs['action'] == 'start':
            result = Torrent.objects.client.start_torrent(torrent.base_id)
        elif kwargs['action'] == 'remove':
            result = Torrent.objects.client.remove_torrent(torrent.base_id)
        elif kwargs['action'] == 'add':
            text = request.GET['text'] if 'text' in request.GET else 'Magnet'
            magnet = "magnet:?xt=urn:btih:" + kwargs['hash'] + "&dn=" + text
            download_dir = _DEFAULT_DIR
            for cat in request.GET['categories'].split():
                if cat in TORRENT_DIRS:
                    download_dir = TORRENT_DIRS[cat]
                    break
            try:
                result = Torrent.objects.client.add_torrent(
                    magnet,
                    download_dir=download_dir
                )
            except Exception as e:
                result = e
        return HttpResponse(result)
