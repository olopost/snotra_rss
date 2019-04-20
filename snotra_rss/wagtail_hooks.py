from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register, ModelAdminGroup
from django.views.generic.base import TemplateView
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.conf import settings
from datetime import datetime, timedelta, date
#from apscheduler.schedulers.background import BackgroundScheduler
#from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from django.utils.timezone import activate
activate(settings.TIME_ZONE)

import time
import logging
import feedparser
import ssl
from time import mktime
from django.views.decorators.csrf import csrf_exempt

from wagtail.core import hooks
from .models import RSSEntries, RSSFeeds, Compte, TwitterConfig

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
if __debug__:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


#from apscheduler.schedulers.background import BackgroundScheduler
#scheduler = BackgroundScheduler()
#from django_apscheduler.jobstores import DjangoJobStore

# If you want all scheduled jobs to use this store by default,
# use the name 'default' instead of 'djangojobstore'.
#scheduler.add_jobstore(DjangoJobStore(), "default")


class RSSFeedsAdmin(ModelAdmin):
    """
        RSS Feeds menu in wagtail admin interface
    """
    model = RSSFeeds
    menu_label = "RSS Feeds"
    menu_icon = "doc-empty-inverse"
    menu_order = 300
    list_display = ('name', 'url', 'active')
    list_filter = ('name', 'url', 'active')
    search_fields = ('name', 'url')



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
    list_display = ('linkurl', 'published', 'update', 'tag')
    list_filter = ['feed', 'tag']
    ordering = ('-update', '-published')

    #fix issues in wagtail for django2.2 fix5106
    from django.contrib.admin import site as default_django_admin_site
    admin_site = default_django_admin_site
    #end fix

class TwitterConfigAdmin(ModelAdmin):
    """
    Twitter config admin
    """
    model = TwitterConfig
    menu_label = "Twitter Config"
    menu_icon = "twitter"
    menu_order = 310

@hooks.register('rssupdate')
def update_rss(request):
    """
    uri for update rss feeds
    :param request: the request query object (parse POST and GET attribute)
    :return: HTTP redirection
    """
    deldate = datetime.now() - timedelta(days=90)
    try:
        logging.debug("Tentative de suppression")
        e = RSSEntries.objects.filter(published__lte=deldate, is_read=True, is_saved=False)
        messages.add_message(request, messages.INFO, str(len(e)) + " messages supprimés")
        for ee in e:
            logging.debug("Suppression de " + ee.title)
        e.delete()
    except Exception as e:
        logging.error("Erreur durant la suppression")
        messages.add_message(request, messages.ERROR, "Erreur durant la suppression")
    feeds = RSSFeeds.objects.filter(active=True)
    for f in feeds:
        start = time.time()
        lfeed = feedparser.parse(f.url)
        end = time.time()
        del_time = end - start
        messages.add_message(request, messages.INFO, str(f.name) + " - temps de parsing : " + str(round(del_time * 1000, 1)) + " ms")
        logging.info(str(f.name) + " nb : " + str(len(lfeed.entries)))
        for e in lfeed.entries:
            logging.debug(e)
            if datetime.fromtimestamp(mktime(e.published_parsed)) < deldate:
                logging.debug("feed < deldate : " + e.title)
                break
            if not hasattr(e, 'id'):
                import hashlib
                e.id = hashlib.sha1(e.title.encode("utf-8")).hexdigest()
            if not RSSEntries.objects.filter(rssid=e.id).exists():
                if not hasattr(e, 'published_parsed'):
                    e.published_parsed = e.updated_parsed
                if not hasattr(e, 'tags'):
                    tags = "no-tags"
                else:
                    tags = e.tags[len(e.tags) - 1].term
                if not hasattr(e, 'link'):
                    link = ""
                else:
                    link = e.link
                if not hasattr(e, 'id'):
                    import hashlib
                    e.id = hashlib.sha1(e.title.encode("utf-8")).hexdigest()
                if hasattr(e, 'content') and hasattr(e, 'title'):
                    em = RSSEntries(feed=f, title=e.title, content=e.content[0].value, rssid=e.id,
                                    published=datetime.fromtimestamp(mktime(e.published_parsed)),
                                    update=datetime.fromtimestamp(mktime(e.updated_parsed)), tag=tags, url=link)
                    em.save()
                else:
                    em = RSSEntries(feed=f, title=e.title, content=e.summary, rssid=e.id,
                                    published=datetime.fromtimestamp(mktime(e.published_parsed)),
                                    update=datetime.fromtimestamp(mktime(e.updated_parsed)), tag=tags, url=link)
                    em.save()

            else:
                logging.debug("rss entry already exist : " + str(e.id))
    return redirect('/admin/snotra_rss/rssentries/')

@csrf_exempt
def feverapi(request):
    """
    fever compatible api for rss aggregator
    :param request: the request query object
    :return: Json response at a format compatible with fever Api
    """
    d = datetime.now()
    logging.debug("--- New request ---")
    logging.debug("POST : " + str(request.POST))
    logging.debug("GET  : " + str(request.GET))
    allowaccount = []
    if 'refresh' in request.GET.keys():
        logging.debug("Update RSS")
        update_rss(request)
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
            logging.debug('get feeds')
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
                entries = RSSEntries.objects.all()
            for e in entries:
                if type(e.published) == type(date(1970, 1, 1)):
                    ontime = (e.published - date(1970, 1, 1)).total_seconds()
                else:
                    ontime = time.mktime(e.published.timetuple())

                ejs = {'id': e.id,
                       'feed_id': e.feed.id,
                       'title': e.title,
                       'url': e.url,
                       'is_read': 0,
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
            logging.debug("Saved : " + str(lu))
        if 'unread_item_ids' in request.GET:
            unread = RSSEntries.objects.filter(is_read=False)
            lu = ""
            for u in unread:
                if lu == "":
                    lu = str(u.id)
                else:
                    lu = lu + "," + str(u.id)
            response['unread_item_ids'] = str(lu)
            logging.debug("Unread : " + str(lu))
        if 'mark' in request.POST and request.POST['mark'] == 'item':
            if 'id' in request.POST.keys() and 'as' in request.POST.keys():
                logging.debug("Mark item " + request.POST['id'] + " as " + request.POST['as'])
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
                    logging.error("Unknown value for Mark item : " + str(request.POST))
                item.save()
        if 'mark' in request.POST and request.POST['mark'] == 'feed':
            if 'id' in request.POST.keys() and 'as' in request.POST.keys():
                logging.debug("Mark feed " + request.POST['id'] + " as " + request.POST['as'])
                item = RSSEntries.objects.filter(feed__id=request.POST['id'])
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
    menu_icon = "book"
    items = (RSSEntriesAdmin, RSSFeedsAdmin, CompteAdmin, TwitterConfigAdmin)

modeladmin_register(Snotra)


#launch scheduler
#register_events(scheduler)
#scheduler.start()
#print("Scheduler started!")