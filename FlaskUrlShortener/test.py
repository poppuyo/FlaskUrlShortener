# boilerplate from https://github.com/realpython/discover-flask/blob/part7/test_boilerplate.md
# helper video at https://www.youtube.com/watch?v=1aHNs1aEATg&feature=youtu.be

import unittest
import sys

from urlshortener import app
from flask import url_for

class FlaskUrlShortenerBasicTestCases(unittest.TestCase):

    # 0 - Basic Diagnostics
    # Ensure that flask was set up correctly
    def test_basic_home(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    # Ensure that we see our prompt
    def test_basic_home_prompt(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertTrue(b'Please enter a URL to shorten' in response.data)

    # Ensure that we are correctly handling a not-yet-existent shortened URL (by returning the main page with error)
    def test_basic_nonexistent_shorturl(self):
        tester = app.test_client(self)
        response = tester.get('/definitelydoesntexistyet', content_type='html/text')
        self.assertTrue(b'Please enter a URL to shorten' in response.data)
        self.assertTrue(b'No match for requested shortened')

    # Ensure that we are shortening a good URL
    def test_basic_good_url(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://google.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)

    # Ensure that we are rejecting a bad (invalid scheme) URL
    def test_basic_bad_url(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="hxxp://12345"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Invalid URL' in response.data)

    # Ensure that we are rejecting an empty (string) URL
    def test_basic_empty_url(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url=""), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Invalid URL' in response.data)

    # Ensure that we are rejecting an empty netloc
    def test_basic_empty_netloc(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Invalid URL' in response.data)


class FlaskUrlShortenerLogicTestCases(unittest.TestCase):

    # 1 - App Logic
    # Ensure that we can submit more than one good URL
    def test_logic_two_good_urls(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://google.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)
        response = tester.post('/add', data=dict(url="http://yahoo.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)

    # Ensure that we can submit and retrieve the URL correctly
    def test_logic_submit_and_retrieve(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://google.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)
        response = tester.get('/get?shortened=Elk6fWZ9', follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'http://google.com' in response.data)

    # Ensure that we can submit and navigate to a stored to a URL correctly
    def test_logic_submit_and_navigate(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://www.bing.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)
        response = tester.get('/7TaXK2ke')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "http://www.bing.com")

    # Ensure that we get the same shortened URL for the same URL
    def test_logic_submit_duplicate_url(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://www.bing.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'/7TaXK2ke' in response.data)
        response = tester.post('/add', data=dict(url="http://www.bing.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'/7TaXK2ke' in response.data)
        # The full encoded token would be '7TaXK2keI0LLcypHCk4zaxVjllaM1a4E2rbk8ibhri3'
        self.assertFalse(b'/7TaXK2keI' in response.data)

    # Ensure that we can't find shortened URLs that haven't been stored yet
    def test_logic_retrieve_nonexistent(self):
        tester = app.test_client(self)
        response = tester.get('/get?shortened=9g4nhd7b2rouv02j4o', follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'No match for requested URL' in response.data)

    # Ensure http vs https uniqueness
    def test_logic_submit_http_https(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://www.bing.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'/7TaXK2ke' in response.data)
        response = tester.post('/add', data=dict(url="https://www.bing.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'/o9OWXFRa' in response.data)

    # Ensure that we can submit and navigate to a stored to a https URL correctly
    def test_logic_submit_and_navigate_https(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="https://www.bing.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)
        response = tester.get('/o9OWXFRa')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "https://www.bing.com")


class FlaskUrlShortenerInputTestCases(unittest.TestCase):
    
    # Ensure that we can submit and navigate to a stored to a URL correctly... in Korean
    def test_input_submit_and_navigate_korean(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url=u"http://한글.한국"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)
        response = tester.get('/DdDP5WSS')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location,"http://xn--bj0bj06e.xn--3e0b707e")


if __name__ == '__main__':
    # multiple test case runs: http://stackoverflow.com/a/16823869
    test_classes_to_run = [FlaskUrlShortenerBasicTestCases, 
                           FlaskUrlShortenerLogicTestCases,
                           FlaskUrlShortenerInputTestCases]

    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)
    ret = not unittest.TextTestRunner(verbosity=2).run(big_suite).wasSuccessful()
    # return an exit code - http://stackoverflow.com/a/24972157
    # returning 0 or other for travis-ci
    sys.exit(ret)
