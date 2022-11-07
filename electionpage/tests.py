"""
Tests for the election pages:
    The general info page exists
        pIndex.html
    You can view election pages
        ps/
        p/
    You can create scrapable election pages
        pCreate/
    You can populate the data in scrapable election pages
        pPopulate/
    You can scrape all elections in an election page
        pScrapeAll

These are more complicated, so we use a live browser to test
so we can play with the javascript and ensure no JS errors,
as well as actually populate data.
"""

import datetime
import time
from urllib.parse import urlparse

from django.core.files import File
from django.urls import reverse
from requests_mock import Mocker
from selenium.common.exceptions import NoSuchElementException

from common.testUtils import TestHelpers
from electionpage.models import ElectionPage, ScrapableElectionPage
from visualizer.models import JsonConfig
from visualizer.tests import filenames
from visualizer.tests import liveServerTestBaseClass


class ElectionPageTests(liveServerTestBaseClass.LiveServerTestBaseClass):
    """ Tests for the electionpage app - using a live browser """
    @classmethod
    def _create_json_config(cls):
        with open(filenames.ONE_ROUND, 'r+') as f:
            return JsonConfig.objects.create(
                jsonFile=File(f),
                title='x',
                numRounds=1,
                numCandidates=1)

    @classmethod
    def _create_election_page(cls, numElections):
        epModel = ElectionPage.objects.create(
            title="Test Election",
            description="Test Description",
            slug="test-slug",
            date=datetime.datetime.utcnow())
        for _ in range(numElections):
            epModel.listOfElections.add(cls._create_json_config())
        return epModel

    @classmethod
    def _create_scrapable_election_page(cls, numElections):
        epModel = ScrapableElectionPage.objects.create(
            title="Test Scrapable Election",
            description="Test Description",
            slug="test-slug",
            date=datetime.datetime.utcnow())
        for _ in range(numElections):
            epModel.listOfScrapers.add(TestHelpers.make_scraper())
        return epModel

    def _provide_all_credentials(self):
        """ These three permissions are sufficient to create and scrape election pages """
        auths = ['add_scraper', 'change_scraper', 'add_scrapableelectionpage']
        self.user = TestHelpers.give_auth(self.user, auths)

    def _fill_in_create_form(self, slug):
        """ After you go to createScrapableElection page, call this to fill out the form """
        self.browser.find_element_by_id("id_slug").send_keys(slug)
        self.browser.find_element_by_id("id_title").send_keys("title")
        self.browser.find_element_by_id("id_date").send_keys("2022-11-06")
        self.browser.find_element_by_id("id_description").send_keys("desc")
        self.browser.find_element_by_id("id_numElections").send_keys("1")

    def test_index(self):
        """ The index page is publicly-viewable and contains the expected # of bullet points """
        self.open(reverse('electionPageHome'))
        self.assertEqual(len(self.browser.find_elements_by_tag_name("li")), 10)

    def test_election_pages(self):
        """ The election pages are error-free for non-scrapable election pages.  """
        epModel = self._create_election_page(numElections=2)
        self.open(reverse('electionPage', args=(epModel.slug,)))

        # Two items
        self.assertEqual(len(self.browser.find_elements_by_class_name("expandableRow")), 2)

        # TODO - add tests here to make sure the four buttons work:
        # 1. Expand bargraph
        # 2. Expand table
        # 3. Open external
        # 4. Click name (default action)
        # Also make sure we click both, and that both iframes become visible

    @Mocker()
    def test_scrape_all(self, requestMock):
        """
        ScrapeAll works, gives the status page corrrectly,
        and the resulting election page shows all successes
        """
        epModel = self._create_scrapable_election_page(numElections=2)
        TestHelpers.mock_scraper_url_with_file(requestMock)
        self._provide_all_credentials()

        # One works, one doesn't
        badScraper = epModel.listOfScrapers.all()[0]
        badScraper.scrapableURL = "mock://bad-url"
        badScraper.save()
        TestHelpers.mock_scraper_url_with_file(requestMock, "mock://bad-url", filenames.BAD_DATA)

        # Results page shows one error, one success
        self.open(reverse('scrapeAll', args=(epModel.slug,)), expectedErrorCount=0)
        self.assertEqual(len(self.browser.find_elements_by_class_name("alert-primary")), 1)
        self.assertEqual(len(self.browser.find_elements_by_class_name("alert-warning")), 1)

        # And the results page should have real data for only one election
        self.open(reverse('scrapableElectionPage', args=(epModel.slug,)))
        listItems = self.browser.find_elements_by_class_name("expandableRow")
        self.assertEqual(len(listItems), 1)
        self.assertEqual(listItems[0].text, 'One round')

    def test_create_scrapable_page_logged_out(self):
        """ Redirect to login if not logged in (don't 403) """
        TestHelpers.logout(self.client)
        self.open(reverse('createScrapableElection'))
        self.assertEqual(urlparse(self.browser.current_url).path, '/accounts/login/')

    def test_create_scrapable_page(self):
        """ With proper permissions, can create a scrapable election page """
        def submit_with_num_elections_and_get_error(num):
            self.browser.find_element_by_id("id_numElections").clear()
            self.browser.find_element_by_id("id_numElections").send_keys(num)
            self.browser.find_element_by_id("submit").click()
            try:
                return self.browser.find_element_by_id(
                    "id_numElections").get_attribute("validationMessage")
            except NoSuchElementException:
                return None

        self._provide_all_credentials()
        self.open(reverse('createScrapableElection'))

        # Hitting submit before filling out the form fails
        self.browser.find_element_by_id("submit").click()
        errorMessage = self.browser.find_element_by_id("id_slug").get_attribute("validationMessage")
        self.assertEqual(errorMessage, "Please fill out this field.")

        # Fill it out, too few elections
        self._fill_in_create_form("cuteslug")

        # Hitting submit should fail with 0 numElections
        self.assertEqual(
            submit_with_num_elections_and_get_error('0'),
            "Value must be greater than or equal to 1.")

        # Hitting submit should fail with >60 numElections
        self.assertEqual(
            submit_with_num_elections_and_get_error('65'),
            "Value must be less than or equal to 60.")

        # Finally, should succeed with 2
        self.assertIsNone(submit_with_num_elections_and_get_error('2'))
        self.assertEqual(urlparse(self.browser.current_url).path, '/pPopulate/cuteslug')

    def test_scrapable_page_slug_must_be_unique(self):
        """ Ensure user cannot create a duplicate slug """
        self._provide_all_credentials()

        # Create one directly into the database
        epModel = self._create_scrapable_election_page(1)
        self.open(reverse('createScrapableElection'))

        # Use the same slug to fill out the form
        self._fill_in_create_form(epModel.slug)
        self.browser.find_element_by_id("submit").click()

        # It should fail with this error message
        errorMessage = self.browser.find_elements_by_class_name("alert-warning")[0].text
        self.assertIn('Scrapable election page with this Slug already exists.', errorMessage)

    def test_auth_forbidden(self):
        """ Each of these pages should 403 if user doen't have permissions """
        epModel = self._create_scrapable_election_page(1)
        self.open(reverse('populateScrapers', args=(epModel.slug,)), expectedErrorCount=1)
        self.assertIn('403', self.browser.page_source)

        self.open(reverse('scrapeAll', args=(epModel.slug,)), expectedErrorCount=1)
        self.assertIn('403', self.browser.page_source)

        self.open(reverse('createScrapableElection'), expectedErrorCount=1)
        self.assertIn('403', self.browser.page_source)

    @Mocker()
    def test_populate(self, requestMock):
        """ Test populate page, and ensure ScrapeAll works """
        TestHelpers.mock_scraper_url_with_file(requestMock)
        TestHelpers.mock_scraper_url_with_file(requestMock, "mock://bad-url", filenames.BAD_DATA)

        epModel = self._create_scrapable_election_page(3)
        self._provide_all_credentials()
        url = reverse('populateScrapers', args=(epModel.slug,))
        self.open(url)

        # Change the second one to an invalid URL
        self.browser.find_element_by_id("id_form-1-scrapableURL").clear()
        self.browser.find_element_by_id("id_form-1-scrapableURL").send_keys("mock://bad-url")

        # After submitting, it should succeed and the page should be the same
        self.browser.find_element_by_id("submit").click()
        self.assertEqual(urlparse(self.browser.current_url).path, url)

        # But the live page should be empty
        self.open(reverse('scrapableElectionPage', args=(epModel.slug,)))
        self.assertEqual(len(self.browser.find_elements_by_class_name("expandableRow")), 0)

        # Until we hit rescrape, then there should be 2/3 valid scrapes
        self.open(reverse('populateScrapers', args=(epModel.slug,)))
        self.browser.find_element_by_id("rescrape").click()
        self.assertEqual(len(self.browser.find_elements_by_class_name("alert-primary")), 2)
        self.assertEqual(len(self.browser.find_elements_by_class_name("alert-warning")), 1)

        # And the live page should have 2 valid elections shown
        self.browser.find_element_by_id("viewlive").click()

        # Refresh (not sure why it's needed)
        self.browser.execute_script("location.reload(true);")
        time.sleep(0.2)  # some breathing room after the refresh

        # There are two valid rows
        self.assertEqual(len(self.browser.find_elements_by_class_name("card")), 2)

    def test_are_results_certified_initializes_correctly(self):
        """ When initialized with areResultsCertified, it propagates to all scrapers """
        self._provide_all_credentials()
        self.open(reverse('createScrapableElection'))

        # Create with certified checked
        self._fill_in_create_form("cuteslug")
        self.browser.find_element_by_id("id_areResultsCertified").click()
        self.browser.find_element_by_id("submit").click()

        for scraper in ScrapableElectionPage.objects.get(slug='cuteslug').listOfScrapers.all():
            self.assertTrue(scraper.areResultsCertified)

    @Mocker()
    def test_are_results_certified_updates_correctly(self, requestMock):
        """ When areResultsCertified updates, it propagates to all scrapers """
        epModel = self._create_scrapable_election_page(numElections=2)
        epModel.areResultsCertified = True
        TestHelpers.mock_scraper_url_with_file(requestMock)
        self._provide_all_credentials()

        # Setting certified updates all models
        epModel.save()
        for scraper in epModel.listOfScrapers.all():
            self.assertTrue(scraper.areResultsCertified)

        # As are the corresponding json configs
        self.open(reverse('scrapeAll', args=(epModel.slug,)))
        for scraper in epModel.listOfScrapers.all():
            self.assertTrue(scraper.jsonConfig.areResultsCertified)
