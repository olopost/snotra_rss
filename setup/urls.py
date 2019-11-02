from django.conf import settings
from django.contrib import admin
from django.conf.urls import include, url
from django.urls import path
from wagtail.admin import urls as wagtailadmin_urls

urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^django-admin/', admin.site.urls),
    path('', include('snotra_rss.urls')),
    path('', include('examples.urls') ),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
