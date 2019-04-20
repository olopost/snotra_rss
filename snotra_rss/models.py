from django.db.models import BooleanField, DateField, Model, CharField, ForeignKey, \
    DO_NOTHING, CASCADE, URLField, TextField, AutoField, EmailField, DateTimeField

class RSSFeeds(Model):
    """
    RSS Feeds Data models
    Feed is view as RSS source

    """
    id = AutoField(primary_key=True)
    name = CharField("Name", max_length=120, null=False)
    url = URLField("URL", null=False)
    active = BooleanField(default=True, null=False)

    class Meta:
        verbose_name = "RSS Feed"
        verbose_name_plural = "RSS Feeds"

    def __str__(self):
        return self.name

class Compte(Model):
    email = EmailField("Email")
    passwd = CharField("Password", max_length=40)

class RSSEntries(Model):
    """
    Rss entries data Models
    Entries is view as rss source article
    """
    title = CharField("Title", max_length=200, null=False)
    content = TextField("Content")
    id = AutoField(primary_key=True)
    rssid = CharField("ID", max_length=200)
    published = DateTimeField("Published")
    update = DateTimeField("Updated")
    tag = CharField("Tag", max_length=100)
    feed = ForeignKey(RSSFeeds, on_delete=CASCADE)
    is_saved = BooleanField(default=False)
    is_read = BooleanField(default=False)
    url = CharField("URL", max_length=200, null=False)

    class Meta:
        verbose_name = "RSS Entry"
        verbose_name_plural = "RSS Entries"

    def linkurl(self):
        from django.utils.html import format_html
        return format_html('<a href="/rss_read?id={}">{}</a>',
                           self.id,
                           self.title)



class TwitterConfig(Model):
    consumer_key = CharField(max_length=40)
    consumer_secret = CharField(max_length=40)
    access_token_key = CharField(max_length=40)
    access_token_secret = CharField(max_length=40)
    class Meta:
        verbose_name = "Twitter Config"
        verbose_name_plural = "Twitter Config"