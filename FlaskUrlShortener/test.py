# boilerplate from https://github.com/realpython/discover-flask/blob/part7/test_boilerplate.md
# helper video at https://www.youtube.com/watch?v=1aHNs1aEATg&feature=youtu.be

import unittest
import sys

from urlshortener import app
#from flask.ext.testing import TestCase

#class BaseTestCase(TestCase):
#    """A base test case."""

#    def create_app(self):
#        app.config.from_object('config.TestConfig')
#        return app
    
#    def setUp(self):




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

    # Ensure that we are correctly handling a not-yet-existent shortened URL (by returning the landing page)
    def test_basic_nonexistent_shorturl(self):
        tester = app.test_client(self)
        response = tester.get('/definitelydoesntexistyet', content_type='html/text')
        self.assertTrue(b'Please enter a URL to shorten' in response.data)

    # Ensure that we are shortening a good URL
    def test_basic_good_url(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="http://google.com"), follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(b'Invalid URL' in response.data)

    # Ensure that we are rejecting a bad URL
    def test_basic_bad_url(self):
        tester = app.test_client(self)
        response = tester.post('/add', data=dict(url="12345"), follow_redirects = True)
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

if __name__ == '__main__':
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(FlaskUrlShortenerBasicTestCases)
    ret = not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    # return an exit code - http://stackoverflow.com/a/24972157
    sys.exit(ret)
