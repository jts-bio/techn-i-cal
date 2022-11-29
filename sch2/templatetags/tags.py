
# imports for django templatetags.py

from django import template
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString 



register = template.Library()


