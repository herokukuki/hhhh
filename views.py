from django.db.models import Q
from django.http import Http404, HttpResponse
from django.views.generic import View, ListView, TemplateView

from torrent.models import Torrent


class TorrentMain(TemplateView):
    """
    Displays torrent app's top page.
    """
    template_name="torrent/torrent.html"


class TorrentList(ListView):
    def get_queryset(self):
        Torrent.objects.sync()
        return Torrent.objects.all()


class TorrentAction(View):
    def get(self, request, *args, **kwargs):
        if kwargs['action'] == 'stop' or kwargs['action'] == 'start':
            try:
                torrent = Torrent.objects.get(base_id=kwargs['id'])
            except Torrent.DoesNotExist as e:
                raise Http404()

        if kwargs['action'] == 'stop':
            result = Torrent.objects.client.stop_torrent(torrent.base_id)
        elif kwargs['action'] == 'start':
            result = Torrent.objects.client.start_torrent(torrent.base_id)
        elif kwargs['action'] == 'add':
            text = request.GET['text'] if 'text' in request.GET else 'Magnet'
            magnet = "magnet:?xt=urn:btih:" + kwargs['hash'] + "&dn=" + text
            result = Torrent.objects.client.add_torrent(magnet)
        return HttpResponse(result)
