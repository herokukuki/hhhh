"""
Models for the Torrent app.
"""
from django.conf import settings
from django.db import models

import transmissionrpc

TRANSMISSION_HOST = getattr(settings, 'TRANSMISSION_HOST', 'localhost')
TRANSMISSION_PORT = getattr(settings, 'TRANSMISSION_PORT', '9091')


class TorrentManager(models.Manager):
    """Manager class for the `Torrent` objects.
    """
    _client = None
    @property
    def client(self):
        if not self._client:
            try:
                self._client = transmissionrpc.Client(TRANSMISSION_HOST,
                                                      port=TRANSMISSION_PORT)
            except transmissionrpc.TransmissionError as e:
                pass
        return self._client

    def get_or_create_from_torrentrpc(self, torrent):
        obj, created = self.get_or_create(base_id=torrent.id)
        obj.name = torrent.name
        obj.date_added = torrent.date_added
        obj.hash = torrent.hashString
        obj.status = torrent.status
        obj.progress = torrent.progress
        obj.save()
        return obj, created

    def sync(self):
        for torrent in self.client.get_torrents():
            obj, craeted = self.get_or_create_from_torrentrpc(torrent)


class Torrent(models.Model):
    """Proxy object for transmissionrpc's Torrent object.
    """
    base_id = models.IntegerField(unique=True)
    hash = models.CharField(max_length=100, default='')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, default='')
    progress = models.FloatField(default=0.0)
    date_added = models.DateTimeField(auto_now=True)
    objects = TorrentManager()

    class Meta:
        ordering = ['date_added']
