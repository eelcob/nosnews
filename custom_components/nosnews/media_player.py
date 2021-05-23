"""NOS News Media Player"""
"""TODO: If possible make link be the pressable link in the card"""

import asyncio
import re
import feedparser
import voluptuous as vol
import logging
from datetime import timedelta
import homeassistant.helpers.config_validation as cv
from homeassistant.components.media_player import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME

from homeassistant.components.media_player.const import (
    MEDIA_TYPE_IMAGE,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_PLAY,
    SUPPORT_PAUSE,
)

from homeassistant.const import STATE_PAUSED, STATE_PLAYING

try:
    from homeassistant.components.media_player import (
        MediaPlayerEntity as MediaPlayerDevice,
    )
except ImportError:
    from homeassistant.components.media_player import MediaPlayerDevice

SUPPORT_NOS = (
    SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PLAY
    | SUPPORT_PAUSE
)

__version__ = "0.0.3"

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ["feedparser"]

CONF_FEED_URL = "feed_url"
CONF_INCLUSIONS = "inclusions"
CONF_EXCLUSIONS = "exclusions"
CONF_SHOW_TOPN = "show_topn"
CONF_MAX_ARTICLES = "articles"

COMPONENT_REPO = "https://github.com/eelcob/nosnews/"

## Time in sec between switching between news items
SCAN_INTERVAL = timedelta(seconds=10)

ICON = "mdi:newspaper-variant"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_FEED_URL): cv.string,
        vol.Required(CONF_MAX_ARTICLES, default=15): cv.positive_int,
        vol.Optional(CONF_SHOW_TOPN, default=9999): cv.positive_int,
        vol.Optional(CONF_INCLUSIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_EXCLUSIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    async_add_devices(
        [
            NOSClient(
                feed=config[CONF_FEED_URL],
                name=config[CONF_NAME],
                articles=config[CONF_MAX_ARTICLES],
                show_topn=config[CONF_SHOW_TOPN],
                inclusions=config[CONF_INCLUSIONS],
                exclusions=config[CONF_EXCLUSIONS],
                number=0,
                counter=0,
            )
        ],
        True,
    )

class NOSClient(MediaPlayerDevice):
    def __init__(
        self,
        feed: str,
        name: str,
        articles: str,
        show_topn: str,
        exclusions: str,
        inclusions: str,
        number: int,
        counter: int,
    ):
        self._feed = feed
        self._name = name
        self._articles = articles
        self._show_topn = show_topn
        self._inclusions = inclusions
        self._exclusions = exclusions
        self._state = None
        self._playing = False
        self._entries = []
        self._number = number
        self._counter = counter

    def update(self):
        if self._counter == 60:
            self._counter = 0

        if self._counter == 0:
            self.feedupdate()

        if self._playing == True:
            self.media_next_track()

        self._counter = self._counter + 1

    def feedupdate(self):
        ##Feedupdate
        parsedFeed = feedparser.parse(self._feed)

        if not parsedFeed:
            _LOGGER.error("Parsing feed failed")
            return False
        else:
            self._state = (
                self._show_topn
                if len(parsedFeed.entries) > self._show_topn
                else len(parsedFeed.entries)
            )
            self._entries = []

            for entry in parsedFeed.entries[: self._state]:
                entryValue = {}
                for key, value in entry.items():
                    if (
                        (self._inclusions and key not in self._inclusions)
                        or ("parsed" in key)
                        or (key in self._exclusions)
                    ):
                        continue

                    entryValue[key] = value

                if 'entity_picture' in self._inclusions and 'entity_picture' not in entryValue.keys():
                    image = []
                    images = []
                    if 'links' in entry.keys():
                        images = re.findall("\'0\', \'href\': \'(.*jpg)", str(entry['links']))
                    if images:
                       entryValue['entity_picture'] = images[0]
                    else:
                       entryValue['entity_picture'] = "https://www.home-assistant.io/images/favicon-192x192-full.png"
                entryValue['media_title'] = entryValue['title']
                entryValue['media_link'] = entryValue['link']

                self._entries.append(entryValue)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        if self._playing == True:
            return STATE_PLAYING
        return STATE_PAUSED

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        key = self.wherearewe()
        return key

    @property
    def media_content_type(self):
        return MEDIA_TYPE_IMAGE

    @property
    def supported_features(self):
        return SUPPORT_NOS

    def wherearewe(self):
        self.checkmin()
        self.checkmax()
        return self.returning()

    def returning(self):
        subnumber = self._number 
        return frozenset(self._entries[subnumber].items())

    def checkmax(self):
        if self._number >= self._articles: 
            self._number = 0

    def checkmin(self):
        if self._number <= -1:
            self._number = self._articles -1

    def media_next_track(self):
        self._number = self._number + 1
        return self.wherearewe()

    def media_previous_track(self):
        self._number = self._number - 1
        return self.wherearewe()

    def media_play_pause(self):
        if self._playing == True:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        self._playing = True
        self._state = STATE_PLAYING
        return self._playing

    def media_pause(self):
        self._state = STATE_PAUSED
        self._playing = False
        return self._playing
