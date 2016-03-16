# urlshortener with flask
# borrows from tutorial code at http://flask.pocoo.org/docs/0.10/tutorial/setup/#tutorial-setup

# imports
import os


if os.environ.get("isHeroku") == '1':
    isProd = True
    import psycopg2 #postgresql for the heroku side
else:
    isProd = False
    import sqlite3 #sqlite for the local side

import logging
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash, Markup
from contextlib import closing
import hashlib
from urllib.parse import urlparse
from baser2 import base62_encode

# create our app
app = Flask(__name__)

# conf
if isProd:
    url = urlparse(os.environ["DATABASE_URL"])
    app.config.update(dict(
        SECRET_KEY = 'devkey'
    ))
else:
    app.config.update(dict(
        DATABASE = os.path.join(app.root_path, 'urls.db'),
        DEBUG = True,
        SECRET_KEY = 'devkey',
        USERNAME = 'admin',
        PASSWORD = 'default',
    ))
    app.config.from_object(__name__)

def connect_db():
    if isProd:
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    else:
        return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource(os.path.join(app.root_path, 'schema.sql'), mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
if not isProd:
    init_db()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_all():
    return render_template('show_all.html')

@app.route('/<path:shortened>')
def find_shortened(shortened):
    if isProd:
        cur = g.db.cursor()
        cur.execute('SELECT url FROM urls WHERE shortened=%s', [shortened]) 
    else:
        cur = g.db.execute('SELECT url FROM urls WHERE shortened=?', [shortened])
    try:
        record = [dict(url=row[0]) for row in cur.fetchall()]
        redirectto = record[0]['url']
        return redirect(redirectto, code=302)
    except:
        return render_template('show_all.html')
    
@app.route('/get', methods=['GET'])
def get_url():
    requested_shortened = request.args.get('shortened')
    # let users put <site>/<shortened> if they want
    requested_shortened = requested_shortened.lstrip(request.url_root)
    if isProd:
        cur = g.db.cursor()
        cur.execute('SELECT url FROM urls where shortened=%s', [requested_shortened])
    else:
        cur = g.db.execute('select url from urls where shortened=?', [requested_shortened])
    try:
        record = [dict(url=row[0]) for row in cur.fetchall()]
        expanded = record[0]['url']
        short_url = request.url_root.rstrip('/') + url_for('find_shortened', shortened=requested_shortened)
        flash(Markup('<a href=' + short_url + '>' + short_url + '</a> expanded to the following URL: <a href=' + expanded + '>' + expanded + '</a>'))
    except:
        flash('No match for requested URL for expanding, try again!')
    return redirect(url_for('show_all'))

@app.route('/add', methods=['POST'])
def add_url():
    # following conventions of treating trailing slashes as pointing to slashless
    # http://stackoverflow.com/questions/5948659/when-should-i-use-a-trailing-slash-in-my-url
    stripped_url = request.form['url'].rstrip(' ').rstrip('/')

    # handle overly long urls
    if len(stripped_url) > 2083:
        urllimit_doc = 'http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers'
        flash(Markup('Please enter a URL <a href=' + urllimit_doc  + '>shorter than 2083</a> characters'))
        return redirect(url_for('show_all'))
    # and overly short ones
    elif len(stripped_url) == 0:
        flash('Invalid URL for shortening, try again!')
        return redirect(url_for('show_all'))

    parsed_url = urlparse(stripped_url)

    # if the user forgot to put a scheme, let's be friendly and assume http
    if not parsed_url.scheme:
        stripped_url = 'http://' + stripped_url
        parsed_url = urlparse(stripped_url)

    # we'll be http or https schemes only
    if (parsed_url.scheme == "http") or (parsed_url.scheme == "https"):
        untrimmed_shortened = shorten(stripped_url)
        leftstring_length = 8

        # 43 is the answer to life, the universe and 'len(base62_encode(int(m.hexdigest(),16)))'
        while leftstring_length <= 43:
            try:
                if isProd:
                    cur = g.db.cursor()
                    # UPSERT-like CTE for postgresql from http://stackoverflow.com/a/8702291
                    cur.execute('WITH new_values (url, shortened) as ( values (%s, %s) ), ' + \
                                'upsert as ' + \
                                  '( update urls u set url = nv.url, shortened = nv.shortened ' + \
                                  ' FROM new_values nv WHERE u.url = nv.url RETURNING u.* )' + \
                                ' INSERT INTO urls (url, shortened) ' + \
                                ' SELECT url, shortened FROM new_values WHERE NOT EXISTS ' + \
                                  ' (SELECT 1 FROM upsert up WHERE up.url = new_values.url)',
                                 [stripped_url, untrimmed_shortened[:leftstring_length]])
                    g.db.commit()
                else:
                    # UPSERT-like behavior http://stackoverflow.com/a/15277374
                    g.db.execute('UPDATE urls SET url=?, shortened=? WHERE url=?', 
                                 [stripped_url, untrimmed_shortened[:leftstring_length], stripped_url])
                    g.db.execute('INSERT OR IGNORE INTO urls (url, shortened) VALUES (?, ?)',
                                 [stripped_url, untrimmed_shortened[:leftstring_length]])
                    g.db.commit()
                short_url = request.url_root + untrimmed_shortened[:leftstring_length]
                flash(Markup('<a href=' + short_url + '>' + short_url + '</a>' + \
                             ' now redirects to the following URL: ' + \
                             '<a href=' + stripped_url + '>' + stripped_url + '</a>'))
                return redirect(url_for('show_all'))
            except:
                # This case handles shortened-URL collisions by inserting with one more character
                leftstring_length += 1

    # if we've gotten here, url shortening has failed
    flash('Invalid URL for shortening, try again!')
    return redirect(url_for('show_all'))

def shorten(url):
    m = hashlib.sha256(url.encode('utf-8'))
    return base62_encode(int(m.hexdigest(), 16))

if __name__ == '__main__':
    app.debug = True
    #grab port from heroku, else be on 5000 as usual
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port)
