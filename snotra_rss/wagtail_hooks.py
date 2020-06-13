from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register, ModelAdminGroup
from django.views.generic.base import TemplateView, RedirectView
from django.http import JsonResponse, QueryDict
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.conf import settings
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from datetime import datetime, timedelta, date
from django.contrib.auth.models import Permission
from django.conf.urls import url
from django.utils.timezone import activate
activate(settings.TIME_ZONE)
import json
from pygelf4ovh import GelfOVHHandler
import socket
import time
import logging
import feedparser
import ssl
from time import mktime
from django.views.decorators.csrf import csrf_exempt
lastrefresh = None
from wagtail.core import hooks
from .models import RSSEntries, RSSFeeds, Compte, TwitterConfig
import sys


def get_client_ip(request):
    """
    To put in util / get client IP
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



class DataDogHandler(logging.handlers.SocketHandler):
    """
    Class to adapt to Datadog Socket Handler
    """
    def __init__(self, host, port):
        logging.handlers.SocketHandler.__init__(self, host, port)

    def makePickle(self, record):
        return (settings.DATADOG_API + ' ' + record.getMessage() + "\n").encode('utf-8')

    def makePickle(self, record):
        return (settings.DATADOG_API + ' ' + record.getMessage() + "\n").encode('utf-8')

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
if settings.DEBUG:
    logger = logging.getLogger('snotra')
    fh = logging.FileHandler(filename="debug.log")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    logger.info("logging mode : debug")
else:
    import logging.handlers
    if settings.DATADOG_LOG:
        logger = logging.getLogger('snotra')
        logger.setLevel(logging.INFO)
        c = logging.StreamHandler()
        sh = DataDogHandler(settings.DATADOG_HOST, settings.DATADOG_PORT)
        sf = logging.Formatter(settings.DATADOG_API + " %(message)s")
        sh.setFormatter(sf)
        c.setFormatter(sf)
        c.setLevel(logging.INFO)
        sh.setLevel(logging.INFO)
        logger.addHandler(sh)
        logger.addHandler(c)
    elif settings.OVH_LOG:
        logger = logging.getLogger('snotra')
        logger.setLevel(logging.INFO)
        import sys
        c = logging.StreamHandler(sys.stdout)
        logger.addHandler(c)
        sh = GelfOVHHandler(host=settings.OVH_URL,
                   port=settings.OVH_PORT, ovh_token=settings.OVH_TOKEN,
                   include_extra_fields=True,
                   debug=True)
        sf = logging.Formatter('%(message)s')
        sh.setFormatter(sf)
        c.setFormatter(sf)
        c.setLevel(logging.DEBUG)
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        logger.propagate = True
    else:
        logging.basicConfig(level=logging.INFO, filename="snotra.log", format='%(asctime)s - %(name)s - %(threadName)s -  %(levelname)s - %(message)s')
        logging.info("logging mode : info")


class RSSFeedsAdmin(ModelAdmin):
    """
        RSS Feeds menu in wagtail admin interface
    """
    model = RSSFeeds
    menu_label = "RSS Feeds"
    menu_icon = "doc-empty-inverse"
    menu_order = 300
    list_display = ('name', 'url', 'active', 'twit')
    list_filter = ('name', 'url', 'active', 'twit')
    search_fields = ('name', 'url')

class UpdateAdmin(RedirectView):
    menu_label = "Update RSS Entries"
    menu_icon = "repeat"
    menu_order = 300
    add_to_settings_menu = False
    permanent = False
    query_string = True
    pattern_name = 'rss update'

    def get_admin_urls_for_registration(self):
        return ()

    def get_redirect_url(self, *args, **kwargs):
        return super().get_redirect_url(*args, **kwargs)

    def will_modify_explorer_page_queryset(self):
        return False


    def get_menu_item(self, order=None):
        return MenuItem('RSS entries update', reverse("rss update"), classnames='icon icon-repeat', order=10000)

    def get_permissions_for_registration(self):
        return Permission.objects.none()

class CompteAdmin(ModelAdmin):
    model = Compte
    menu_label = "RSS Feeds Account"
    menu_icon = "user"
    menu_order = 300

class RSSEntriesAdmin(ModelAdmin):
    """
    Wagtail admin interface for rss entries
    """
    model = RSSEntries
    menu_label = "RSS Entries"
    menu_icon = "doc-empty-inverse"
    menu_order = 300
    list_display = ('linkurl', 'published', 'update', 'tag_list')
    list_filter = ['feed', 'tags']
    ordering = ('-update', '-published')

    #fix issues in wagtail for django2.2 fix5106
    from django.contrib.admin import site as default_django_admin_site
    admin_site = default_django_admin_site
    #end fix


    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

class TwitterConfigAdmin(ModelAdmin):
    """
    Twitter config admin
    """
    model = TwitterConfig
    menu_label = "Twitter Config"
    menu_icon = "cogs"
    menu_order = 310

import threading
LOCALE_LOCK = threading.Lock()
from contextlib import contextmanager

@contextmanager
def setlocale(name):
    import locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

@hooks.register('twitupdate')
def update_twitter(request):
    import twitter
    logger.info("new request to twitter", extra={"client_ip": get_client_ip(request)})
    e = TwitterConfig.objects.get()
    try:
        myapi = twitter.Api(consumer_key=str(e.consumer_key),
                          consumer_secret=str(e.consumer_secret),
                          access_token_key=str(e.access_token_key),
                          access_token_secret=str(e.access_token_secret))
    except twitter.TwitterError as err:
        logger.error("Twitter init error : " + str(err))
    feeds = RSSFeeds.objects.filter(active=True, twit=True)
    for f in feeds:
        if f.name[0] == '@':
            api_iter = myapi.GetUserTimeline(screen_name=f.name)
        else:  # f.name[0] == '#':
            api_iter = myapi.GetSearch(f.name,count=10)
        for twit in api_iter:
            import json
            with setlocale('C'):
                ldate = datetime.strptime(twit.created_at, "%a %b %d %H:%M:%S %z %Y")
                mytag = []
                for i in twit.hashtags:
                    ltag = json.loads(str(i))['text']
                    mytag.append(ltag)
                if len(twit.urls) > 0:
                    myurl = twit.urls[0].url
                else:
                    myurl = ""
                import re
                url_r = re.compile(r'(https://[^ ]+)', re.IGNORECASE)
                if re.search(url_r, twit.text):
                    twit_content = url_r.sub(r'<a href="\1">\1</a>', twit.text)
                    twit_title = url_r.sub('', twit.text)
                else:
                    twit_content = twit.text
                    twit_title = twit.text[0:80]
                url_r = re.compile(r'(@[^ ]+)', re.IGNORECASE)
                if re.search(url_r, twit_title):
                    twit_title = url_r.sub('', twit_title)
                url_r = re.compile(r'(#[^ ]+)', re.IGNORECASE)
                tags = re.findall(url_r, twit.text)
                for t in tags:
                    mytag.append(t[1:])
                if not RSSEntries.objects.filter(rssid=twit.id).exists():
                    em = RSSEntries(feed=f, title=twit_title, content=twit_content, rssid=twit.id,
                                published=ldate, update=ldate, url=myurl)
                    for t in mytag:
                        em.tags.add(t)
                    em.save()
                    if em.url == "":
                        em.url = request.build_absolute_uri('/rss_read/?id=' + str(em.id))
                        em.save()
    return redirect('/admin/snotra_rss/rssentries/')

@hooks.register('rssupdate')
def update_rss(request):
    """
    uri for update rss feeds
    :param request: the request query object (parse POST and GET attribute)
    :return: HTTP redirection
    """
    deldate = datetime.now() - timedelta(days=90)
    logger.info("new request to update rss", extra={"client_ip": get_client_ip(request)})
    try:
        logger.debug("Tentative de suppression")
        e = RSSEntries.objects.filter(published__lte=deldate, is_read=True, is_saved=False)
        messages.add_message(request, messages.INFO, str(len(e)) + " messages supprimés")
        for ee in e:
            logger.debug("Suppression de " + ee.title)
        e.delete()
    except Exception as e:
        messages.add_message(request, messages.ERROR, f"Erreur durant la suppression: {e}")
    feeds = RSSFeeds.objects.filter(active=True,twit=False)
    for f in feeds:
        start = time.time()
        socket.setdefaulttimeout(2)
        try:
            lfeed = feedparser.parse(f.url)
        except socket.timeout:
            messages.add_message(request, messages.ERROR, "Erreur de timeout : " + str(f.name))
        end = time.time()
        del_time = end - start
        messages.add_message(request, messages.INFO, str(f.name) + " - temps de parsing : " + str(round(del_time * 1000, 1)) + " ms")
        for e in lfeed.entries:
            logger.debug(e)
            if not hasattr(e, 'published_parsed') or e.published_parsed is None:
                e.published_parsed = datetime.now().timetuple()
            if datetime.fromtimestamp(mktime(e.published_parsed)) < deldate:
                logger.debug("feed < deldate : " + e.title)
                break
            if not hasattr(e, 'id'):
                import hashlib
                e.id = hashlib.sha1(e.title.encode("utf-8")).hexdigest()
            mytag = []
            if not RSSEntries.objects.filter(rssid=e.id).exists():
                if not hasattr(e, 'updated_parsed') or e.updated_parsed is None:
                    e.updated_parsed = datetime.now().timetuple()
                if not hasattr(e, 'published_parsed') or e.published_parsed is None:
                    e.published_parsed = e.updated_parsed
                if not hasattr(e, 'tags'):
                    pass
                else:
                    for i in e.tags:
                        if hasattr(i, 'term'):
                            mytag.append(str(i.term))
                        else:
                            messages.add_message(request, messages.ERROR, f'{ e } as no term attibute')
                if not hasattr(e, 'link'):
                    link = ""
                else:
                    link = e.link[:200]
                if not hasattr(e, 'id'):
                    import hashlib
                    e.id = hashlib.sha1(e.title.encode("utf-8")).hexdigest()
                else:
                    e.id = e.id[:200]
                if hasattr(e, 'content') and hasattr(e, 'title'):
                    em = RSSEntries(feed=f, title=e.title[:200], content=e.content[0].value, rssid=e.id,
                                    published=datetime.fromtimestamp(mktime(e.published_parsed)),
                                    update=datetime.fromtimestamp(mktime(e.updated_parsed)), url=link)
                    em.save()
                else:
                    em = RSSEntries(feed=f, title=e.title[:200], content=e.summary, rssid=e.id,
                                    published=datetime.fromtimestamp(mktime(e.published_parsed)),
                                    update=datetime.fromtimestamp(mktime(e.updated_parsed)), url=link)
                    em.save()
                if em.url == "":
                    em.url = request.build_absolute_uri('/rss_read/?id=' + str(em.id))
                    em.save()
                if len(mytag) > 0:
                    for t in mytag:
                        em.tags.add(t)
                    em.save()

            else:
                logger.debug("rss entry already exist : " + str(e.id))
    return redirect('/admin/snotra_rss/rssentries/')


@csrf_exempt
def feverapi(request):
    global lastrefresh
    """
    fever compatible api for rss aggregator
    :param request: the request query object
    :return: Json response at a format compatible with fever Api
    """
    d = datetime.now()
    logger.info("new request to fever", extra={"client_ip": get_client_ip(request)})
    if request.POST:
        logger.info("POST receive : %s", request.POST.dict())
    if request.GET:
        logger.info("POST receive : %s", request.GET.dict())
    allowaccount = []
    if 'refresh' in request.GET.keys() and (lastrefresh is None or (d - lastrefresh).total_seconds() > 120) :
        update_rss(request)
        update_twitter(request)
        lastrefresh = d
    for c in Compte.objects.all():
        import hashlib
        m = hashlib.md5()
        myhash = str(c.email) + ":" + str(c.passwd)
        m.update(myhash.encode('utf-8'))
        allowaccount.append(m.hexdigest())
    response = {}
    if 'api_key' in request.POST.keys() and request.POST['api_key'] in allowaccount:
        response['api_version'] = 3.0
        response['auth'] = 1
        if 'groups' in request.GET:
            mygroups = [{'id': 1, 'title': 'SnotraRSS'}]
            response['groups'] = mygroups
        if 'feeds' in request.GET:
            myfeed = []
            myfeedgroup = []
            for f in RSSFeeds.objects.all():
                fjs = {'id': str(f.id),
                                  'favicon_id': 1,
                                  'title': f.name,
                                  'url': f.url,
                                  'site_url': f.url,
                                  'is_spark': 0,
                                  'last_update_on_time': (d - datetime(1970,1,1)).total_seconds()}
                fgjs = {'group_id': 1, 'feed_ids': str(f.id)}
                myfeed.append(fjs)
                myfeedgroup.append(fgjs)
                response['feeds'] = myfeed
                response['feeds_groups'] = myfeedgroup
        myitems = []
        if 'items' in request.GET:
            if 'since_id' in request.GET.keys():
                entries = RSSEntries.objects.filter(id__gt=int(request.GET['since_id']))
            else:
                entries = RSSEntries.objects.all()[:50]
            for e in entries:
                if type(e.published) == type(date(1970, 1, 1)):
                    ontime = (e.published - date(1970, 1, 1)).total_seconds()
                else:
                    ontime = time.mktime(e.published.timetuple())

                ejs = {'id': e.id,
                       'feed_id': e.feed.id,
                       'title': e.title,
                       'url': e.url,
                       'is_read': int(e.is_read),
                       'html': e.content,
                       'created_on_time': ontime}
                myitems.append(ejs)
                response['items'] = myitems
        if 'saved_item_ids' in request.GET:
            star = RSSEntries.objects.filter(is_saved=True)
            lu = ""
            for u in star:
                if lu == "":
                    lu = str(u.id)
                else:
                    lu = lu + "," + str(u.id)
            response['saved_item_ids'] = str(lu)
        if 'unread_item_ids' in request.GET:
            # limitation to 50 in order to avoid invalid request block size
            unread = RSSEntries.objects.filter(is_read=False)[:50]
            lu = ""
            for u in unread:
                if lu == "":
                    lu = str(u.id)
                else:
                    lu = lu + "," + str(u.id)
            response['unread_item_ids'] = str(lu)
        if 'mark' in request.POST and request.POST['mark'] == 'item':
            if 'id' in request.POST.keys() and 'as' in request.POST.keys():
                item = RSSEntries.objects.get(id=request.POST['id'])
                if request.POST['as'] == 'read':
                    item.is_read = True
                elif request.POST['as'] == 'unread':
                    item.is_read = False
                elif request.POST['as'] == 'saved':
                    item.is_saved = True
                elif request.POST['as'] == 'unsaved':
                    item.is_saved = False
                else:
                    logger.error('fever', "Unknown value for Mark item : " + str(request.POST))
                item.save()
        if 'mark' in request.POST and request.POST['mark'] == 'feed':
            if 'id' in request.POST.keys() and 'as' in request.POST.keys():
                item = RSSEntries.objects.filter(feed__id=request.POST['id'])
                with transaction.atomic():
                    if request.POST['as'] == 'read':
                        for i in item:
                            i.is_read = True
                            i.save()
        if 'mark' in request.POST and request.POST['mark'] == 'group':
            if 'id' in request.POST.keys() and 'as' in request.POST.keys():
                item = RSSEntries.objects.filter(feed_id__gte=request.POST['id'])
                with transaction.atomic():
                    if request.POST['as'] == 'read':
                        for i in item:
                            i.is_read = True
                            i.save()
        return JsonResponse(response)
    else:
        return JsonResponse({})


class ConsultRss(TemplateView):
    """
    Web page for rss entries viewing
    """
    template_name = "base/update.html"
    feeds = RSSFeeds.objects.all()
    entries = RSSEntries.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feeds'] = self.feeds
        context['entries'] = RSSEntries.objects.filter(id=self.request.GET['id'])
        return context

class Snotra(ModelAdminGroup):
    menu_label = "Snotra"
    menu_icon = "snotra"
    items = (RSSEntriesAdmin, RSSFeedsAdmin, CompteAdmin, TwitterConfigAdmin, UpdateAdmin)

modeladmin_register(Snotra)


#launch scheduler
#register_events(scheduler)
#scheduler.start()
