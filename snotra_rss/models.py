from django.db.models import BooleanField, DateField, Model, CharField, ForeignKey, \
    DO_NOTHING, CASCADE, URLField, TextField

class RSSFeeds(Model):
    """
    RSS Feeds Data models
    Feed is view as RSS source

    """
    name = CharField("Name", max_length=120, null=False)
    url = URLField("URL", null=False)
    active = BooleanField(default=True, null=False)

    class Meta:
        verbose_name = "RSS Feed"
        verbose_name_plural = "RSS Feeds"

    def __str__(self):
        return self.name


class RSSEntries(Model):
    """
    Rss entries data Models
    Entries is view as rss source article
    """
    title = CharField("Title", max_length=200, null=False)
    content = TextField("Content")
    rssid = CharField("ID", max_length=200)
    published = DateField("Published")
    update = DateField("Updated")
    tag = CharField("Tag", max_length=100)
    feed = ForeignKey(RSSFeeds, on_delete=CASCADE)

    class Meta:
        verbose_name = "RSS Entry"
        verbose_name_plural = "RSS Entries"

    def linkurl(self):
        from django.utils.html import format_html
        return format_html('<a href="/rss_read?id={}">{}</a>',
                           self.id,
                           self.title)


