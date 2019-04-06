from django.conf import settings
from django.contrib import admin
from django.conf.urls import include, url
from wagtail.admin import urls as wagtailadmin_urls
from .wagtail_hooks import update_rss, ConsultRss, feverapi

urlpatterns = [
    #url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^update/$', update_rss, name='rss update'),
    url(r'^rss_read/$', ConsultRss.as_view(), name='rss update'),
    url(r'^fever/$', feverapi, name="feverapi"),
    url(r'^django-admin/', admin.site.urls),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
