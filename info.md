NOS News media player, configurable to a max of 20 latest news articles.
Can be configured to play which rotates news items every 10 seconds.
Manual forward and backward in the media player also possible.

Add the following integration to your configuration:

media_player:
  - platform: nosnews
    name: NOS Feed
    feed_url: 'http://feeds.nos.nl/nosnieuwsalgemeen'
    articles: 17
    inclusions:
      - title
      - entity_picture
      - link


