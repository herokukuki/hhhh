"""
Models for the Torrent app.
"""
from django.conf import settings
from django.db import models

import transmissionrpc

TRANSMISSION_HOST = getattr(settings, 'TRANSMISSION_HOST', 'localhost')
TRANSMISSION_PORT = getattr(settings, 'TRANSMISSION_PORT', '9091')
TRANSMISSION_USER = getattr(settings, 'TRANSMISSION_USER', None)
TRANSMISSION_PASS = getattr(settings, 'TRANSMISSION_PASS', None)


class TorrentManager(models.Manager):
    """Manager class for the `Torrent` objects.
    """
    _client = None
    @property
    def client(self):
        if not self._client:
            try:
                self._client = transmissionrpc.Client(
                    address=TRANSMISSION_HOST,
                    port=TRANSMISSION_PORT,
                    user=TRANSMISSION_USER,
                    password=TRANSMISSION_PASS
                )
            except transmissionrpc.TransmissionError as e:
                pass
        return self._client

    def get_or_create_from_torrentrpc(self, torrent):
        obj, created = self.get_or_create(base_id=torrent.id)
        dirty = False
        if obj.name != torrent.name:
            obj.name = torrent.name
            dirty = True
        if obj.date_added != torrent.date_added:
            obj.date_added = torrent.date_added
            dirty = True
        if obj.hash != torrent.hashString:
            obj.hash = torrent.hashString
            dirty = True
        if obj.status != torrent.status:
            obj.status = torrent.status
            dirty = True
        if obj.progress != torrent.progress:
            obj.progress = torrent.progress
            dirty = True
        if obj.deleted:
            obj.deleted = False
            dirty = True
        if dirty:
            obj.save()
        return obj, created

    def sync(self):
        ids = []
        for torrent in self.client.get_torrents():
            ids.append(torrent.id)
            obj, craeted = self.get_or_create_from_torrentrpc(torrent)
        self.exclude(base_id__in=ids).update(deleted=True)

    def active(self):
        qs = super(TorrentManager, self).get_query_set()
        return qs.filter(deleted=False)


class Torrent(models.Model):
    """Proxy object for transmissionrpc's Torrent object.
    """
    base_id = models.IntegerField(unique=True)
    hash = models.CharField(max_length=100, default='')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='')
    progress = models.FloatField(default=0.0)
    date_added = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    objects = TorrentManager()

    class Meta:
        ordering = ['-date_added']

    def progress_css_class(self):
        if self.status == 'downloading':
            return 'progress-striped active'
        if self.status == 'seeding':
            return 'progress-success'
        if self.status == 'stopped':
            return 'progress-disabled'
        return ''

    def fields(self):
        return self.base()._fields

    def base(self):
        return Torrent.objects.client.get_torrent(self.base_id)
