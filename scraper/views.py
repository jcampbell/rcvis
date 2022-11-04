"""
Scraper views:
    both the worker to scrape now,
    and the page with all info about the scraper.
All of these are limited to authorized users.
"""
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import DetailView

from scraper.models import Scraper
from scraper.scrapeWorker import ScrapeWorker


class ViewScraper(PermissionRequiredMixin, DetailView):
    """ Visualizing a single JsonConfig """
    model = Scraper
    template_name = 'scraper/scrape.html'
    permission_required = 'scraper.view_scraper'


class ScrapeNow(PermissionRequiredMixin, DetailView):
    """ Visualizing a single JsonConfig """
    model = Scraper
    template_name = 'scraper/scrapeNow.html'
    permission_required = ['scraper.add_scraper', 'scraper.change_scraper']

    def get(self, *args, **kwargs):
        try:
            scraperObject = self.get_object()
            user = self.request.user
            ScrapeWorker.scrape(scraperObject, user)
            return redirect(reverse('viewScraper', kwargs=kwargs))
        except BaseException:  # pylint: disable=broad-except
            return redirect(reverse('viewScraper', kwargs=kwargs))
