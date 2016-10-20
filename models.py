"""
Models for the Torrent app.
"""
from datetime import timedelta, datetime
import dateutil.tz
import os
import re
import logging

from django.conf import settings
from django.db import models

import transmissionrpc

TRANSMISSION_HOST = getattr(settings, 'TRANSMISSION_HOST', 'localhost')
TRANSMISSION_PORT = getattr(settings, 'TRANSMISSION_PORT', '9091')
TRANSMISSION_USER = getattr(settings, 'TRANSMISSION_USER', None)
TRANSMISSION_PASS = getattr(settings, 'TRANSMISSION_PASS', None)
TRANSMISSION_DOWNLOAD_ROOT = getattr(settings, 'TRANSMISSION_DOWNLOAD_ROOT',
                                     settings.MEDIA_ROOT)
TRANSMISSION_DOWNLOAD_URL = getattr(settings, 'TRANSMISSION_DOWNLOAD_URL',
                                    settings.MEDIA_URL)

DEFAULT_DIR = os.path.join(TRANSMISSION_DOWNLOAD_ROOT, 'downloads')
_DEFAULT_DIRS = [
    ('music', os.path.join(TRANSMISSION_DOWNLOAD_ROOT, 'music')),
    ('movie', os.path.join(TRANSMISSION_DOWNLOAD_ROOT, 'movies')),
    ('tv', os.path.join(TRANSMISSION_DOWNLOAD_ROOT, 'tv')),
    ('ebooks', os.path.join(TRANSMISSION_DOWNLOAD_ROOT, 'ebooks')),
    ('ebook', os.path.join(TRANSMISSION_DOWNLOAD_ROOT, 'ebooks')),
]
TORRENT_DIRS = getattr(settings, 'TORRENT_DIRS', [])
TORRENT_DIRS += _DEFAULT_DIRS


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
                logging.exception(e)
                pass
        return self._client

    def get_or_create_from_torrentrpc(self, torrent):
        obj, created = self.get_or_create(hash=torrent.hashString)
        dirty = False
        if obj.name != torrent.name:
            obj.name = torrent.name
            dirty = True
        d = torrent.date_added
        # Offset back to UTC
        if d.tzinfo:
            d = d.astimezone(dateutil.tz.tzutc())
        else:
            d = d.replace(tzinfo=dateutil.tz.tzutc())
        if not settings.USE_TZ:
            d = d.replace(tzinfo=None)
        if obj.date_added != d:
            obj.date_added = d
            dirty = True
        if obj.base_id != torrent.id:
            obj.base_id = torrent.id
            dirty = True
        if obj.status != torrent.status:
            obj.status = torrent.status
            dirty = True
        if abs(obj.progress - torrent.progress) > 0.0001:
            obj.progress = torrent.progress
            dirty = True

        if obj.progress == 100.0 and obj.status in ['stopped', 'seeding']:
            download_dir = obj.download_dir().rstrip(os.sep)
            for d in TORRENT_DIRS:
                if d[1] != download_dir:
                    # These are not the droids you are looking for, move along
                    continue
                if len(d) > 3:
                    secs = d[3]
                    now = datetime.now()
                    if obj.base().date_done + timedelta(seconds=secs) < now:
                        # Past the expiration date
                        logging.info('%s has expired, removing', obj)
                        result = self.client.remove_torrent(obj.base_id)
                        logging.info('Result: %s', result)
                        obj.deleted = True
                        obj.base_id = -1
                        dirty = True
                        break
                if len(d) > 2:
                    secs = d[2]
                    now = datetime.now()
                    if obj.base().date_done + timedelta(seconds=secs) < now:
                        # Past the expiration date
                        if not obj.deleted:
                            logging.info('%s has expired, ignoring', obj)
                            obj.deleted = True
                            dirty = True
                            break
        elif obj.deleted:
            obj.deleted = False
            dirty = True

        if dirty:
            logging.info('Updating %s', obj)
            obj.save()
        return obj, created

    def sync(self):
        hashes = []
        for torrent in self.client.get_torrents():
            logging.debug('Processiong %s', torrent)
            obj, craeted = self.get_or_create_from_torrentrpc(torrent)
            if not obj.deleted:
                hashes.append(torrent.hashString)
        qs = self.exclude(hash__in=hashes).exclude(deleted=True)
        updated = qs.update(deleted=True, base_id=-1)
        if updated > 0:
            logging.info('Removed %d torrent(s)', updated)

    def active(self):
        qs = super(TorrentManager, self).get_query_set()
        return qs.filter(deleted=False)


class Torrent(models.Model):
    """Proxy object for transmissionrpc's Torrent object.
    """
    base_id = models.IntegerField(default=-1)
    hash = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='')
    progress = models.FloatField(default=0.0)
    date_added = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    owners = models.ManyToManyField('auth.User', null=True, blank=True)
    objects = TorrentManager()

    class Meta:
        ordering = ['-date_added']

    def __unicode__(self):
        return '%d: %s, %s, %s' % (
            self.base_id, self.name, self.hash, self.owners.all())

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

    def download_dir(self):
        return self.fields()['downloadDir'].value

    def file_url(self):
        return '/'.join([
            re.sub(
                TRANSMISSION_DOWNLOAD_ROOT.rstrip(os.sep),
                TRANSMISSION_DOWNLOAD_URL.rstrip('/'),
                self.download_dir()
            ).replace('\\', '/'),
            self.name
        ])
