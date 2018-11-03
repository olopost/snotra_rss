from django.conf.urls import url
from django.urls import reverse

from wagtail.core import hooks
from wagtail.admin.menu import MenuItem
from ..models import RSSEntriesAdmin

@hooks.register('register_admin_menu_item'):
def register_menu_item():
    return MenuItem('RSS Entries', reverse(RSSEntriesAdmin))