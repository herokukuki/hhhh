from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.views.generic import View, ListView, DetailView

from torrent.models import Torrent

_DEFAULT_DIR = '/home/media/downloads/'
_DEFAULT_DIRS = {
    'music': '/home/media/mlib',
    'movie': '/home/media/mov/Movies',
    'tv': '/home/media/mov/TV',
}
TORRENT_DIRS = getattr(settings, 'TORRENT_DIRS', _DEFAULT_DIRS)


class TorrentList(ListView):
    def get_template_names(self, queryset=None):
        if self.kwargs['format'] == 'json':
            return ['torrent/torrent_list.json']
        else:
            return ['torrent/torrent_list.html']

    def get_queryset(self):
        if self.request.user.has_perm('torrent.change_torrent'):
            Torrent.objects.sync()
            qs = Torrent.objects.active()
            if self.request.user.is_superuser:
                return qs
            return qs.filter(owners=self.request.user)
        return Torrent.objects.none()


class TorrentDetail(DetailView):
    model = Torrent
    slug_field = 'base_id'
    slug_url_kwarg = 'id'

    def get_template_names(self, queryset=None):
        if self.request.is_ajax():
            return ['torrent/torrent_detail_ajax.html']
        else:
            return ['torrent/torrent_detail.html']


class TorrentAction(View):
    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('torrent.change_torrent'):
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
            if self.request.user.is_superuser:
                result = Torrent.objects.client.remove_torrent(torrent.base_id)
            else:
                torrent.owners.remove(self.request.user)
                torrent.save()
                result = torrent
        elif kwargs['action'] == 'add':
            text = request.GET['text'] if 'text' in request.GET else 'Magnet'
            magnet = "magnet:?xt=urn:btih:" + kwargs['hash'] + "&dn=" + text
            download_dir = _DEFAULT_DIR
            for cat in request.GET['categories'].split():
                if cat in TORRENT_DIRS:
                    download_dir = TORRENT_DIRS[cat]
                    break
            torrent = None
            try:
                base = Torrent.objects.client.add_torrent(
                    magnet,
                    download_dir=download_dir
                )
                torrent, _c = Torrent.objects.get_or_create(
                    hash=kwargs['hash'])
                result = base
            except Exception as e:
                try:
                    torrent = Torrent.objects.get(hash=kwargs['hash'])
                except Torrent.DoesNotExist as e:
                    result = e
                else:
                    result = torrent
            if torrent:
                torrent.owners.add(self.request.user)
                torrent.save()
        return HttpResponse(result)
