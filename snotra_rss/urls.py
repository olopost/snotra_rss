from django.conf import settings
from django.conf.urls import include, url
from snotra_rss.wagtail_hooks import update_rss, ConsultRss, feverapi, update_twitter

urlpatterns = [
    url(r'^update/$', update_rss, name='rss update'),
    url(r'^twitupdate/$', update_twitter, name='twit update'),
    url(r'^rss_read/$', ConsultRss.as_view(), name='rss read'),
    url(r'^fever/$', feverapi, name="feverapi"),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
