from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.views.generic import View, ListView

from torrent.models import Torrent


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
            try:
                result = Torrent.objects.client.add_torrent(magnet)
            except Exception as e:
                result = e
        return HttpResponse(result)
