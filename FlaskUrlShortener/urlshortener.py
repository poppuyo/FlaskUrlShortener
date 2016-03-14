# urlshortener with flask
# borrows from tutorial code at http://flask.pocoo.org/docs/0.10/tutorial/setup/#tutorial-setup

# imports
import os

if os.environ.get("isHeroku") == '1':
    isProd = True
    import psycopg2
else:
    isProd = False
    import sqlite3

import logging
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
import hashlib
from urllib.parse import urlparse

from baser import base_encode
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
    if isProd:
       cur = g.db.cursor()
       cur.execute('select * from urls order by id desc limit 1')
       g.db.commit()
    else:
       cur = g.db.execute('select * from urls order by id desc limit 1')
    records = [dict(id=row[0], url=row[1], shortened=row[2]) for row in cur.fetchall()]
    return render_template('show_all.html', records=records)

@app.route('/<path:shortened>')
def find_shortened(shortened):
    if isProd:
        cur = g.db.cursor()
        cur.execute('SELECT url FROM urls where shortened=%s', [shortened]) 
    else:
        cur = g.db.execute('select url from urls where shortened=?', [shortened])
    try:
        record = [dict(url=row[0]) for row in cur.fetchall()]
        redirectto = record[0]['url']
        return redirect(redirectto, code=302)
    except:
        if isProd:
            cur = g.db.cursor()
            cur.execute('SELECT * from urls order by id desc limit 1')
        else:
            cur = g.db.execute('select * from urls order by id desc limit 1')
        records = [dict(id=row[0], url=row[1], shortened=row[2]) for row in cur.fetchall()]
        return render_template('show_all.html', records=records)
    
@app.route('/get', methods=['GET'])
def get_url():
    requested_shortened = request.args.get('shortened')
    if isProd:
        cur = g.db.cursor()
        cur.execute('SELECT url FROM urls where shortened=%s', [requested_shortened])
    else:
        cur = g.db.execute('select url from urls where shortened=?', [requested_shortened])
    try:
        record = [dict(url=row[0]) for row in cur.fetchall()]
        expanded = record[0]['url']
        flash(url_for('find_shortened', shortened=requested_shortened) + ' expanded to the following URL: ' + expanded)
    except:
        flash('No match for requested URL for expanding, try again!')
    return redirect(url_for('show_all'))

@app.route('/add', methods=['POST'])
def add_url():
    stripped_url = request.form['url'].rstrip().rstrip("/")
    parsed_url = urlparse(stripped_url)

    if (parsed_url.scheme == "http") or (parsed_url.scheme == "https"):
        untrimmed_shortened = shorten(stripped_url)
        leftstring_length = 8

        while True:
            try:
                if isProd:
                    cur = g.db.cursor()
                    print("started")
                    print(leftstring_length)
                    # crazy upsert CTE from http://stackoverflow.com/a/8702291
                    cur.execute('WITH new_values (url, shortened) as ( values (%s, %s) ), upsert as ( update urls u set url = nv.url, shortened = nv.shortened FROM new_values nv WHERE u.url = nv.url RETURNING u.* ) INSERT INTO urls (url, shortened) SELECT url, shortened FROM new_values WHERE NOT EXISTS (SELECT 1 FROM upsert up WHERE up.url = new_values.url)', [stripped_url, untrimmed_shortened[:leftstring_length]])
                    # less safe upsert-like from http://stackoverflow.com/a/6527838
                    #cur.execute('UPDATE urls SET url=%s, shortened=%s where url=%s', [stripped_url, untrimmed_shortened[:leftstring_length], stripped_url])
                    #cur.execute('INSERT INTO urls (url, shortened) SELECT %s, %s WHERE NOT EXISTS (SELECT 1 FROM urls where url=%s)', [stripped_url, untrimmed_shortened[:leftstring_length], stripped_url])
                    g.db.commit()
                else:
                    # UPSERT-like behavior http://stackoverflow.com/a/15277374
                    g.db.execute('UPDATE urls SET url=?, shortened=? WHERE url=?', [stripped_url, untrimmed_shortened[:leftstring_length], stripped_url])
                    g.db.execute('INSERT OR IGNORE INTO urls (url, shortened) VALUES (?, ?)', [stripped_url, untrimmed_shortened[:leftstring_length]])
                    g.db.commit()
                flash('New url was successfully entered')
                break
            except:
                # let's get a longer shortened string
                leftstring_length += 1
                break
    else:
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
