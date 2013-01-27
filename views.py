from django.db.models import Q
from django.views.generic import ListView, TemplateView

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
