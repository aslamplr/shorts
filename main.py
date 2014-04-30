"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask import Flask, Response
from flask import g, session, request, redirect \
                  , render_template, render_template_string, Markup \
                  , flash, url_for, abort, escape \
                  , jsonify

from flask_oauthlib.client import OAuth, OAuthException
from functools import wraps

from google.appengine.ext import ndb

FACEBOOK_APP_ID = '1389300194684954'
FACEBOOK_APP_SECRET = 'e6dd54716a481a45cbb7195dfdf1b284'

app = Flask(__name__)
app.secret_key = "dev_secret_key_for_shorts-store"
oauth = OAuth(app)

facebook = oauth.remote_app(
    'facebook',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth'
)

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'oauth_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

import new, shorts, youtube_crawler

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return redirect(url_for('hello_knockout'))

@app.route('/index.html')
@app.route('/index/')
def hello_knockout():
    return render_template("knockout.html",title='The short film finder')

@app.route('/knockout/')
def hello_knockout_test():
    return render_template("knockout_test.html",title='The short film finder')
	
@app.route('/favicon.ico')
def favicon():
    with open('static/images/favicon.ico') as icon:
        return Response(icon.read(),200,
                    {'Content-Type': 'image/x-icon'})

@app.route('/login')
def login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return facebook.authorize(callback=callback)

@app.route('/logout')
def logout():
    session.pop('oauth_token',None)
    session.pop('me',None)
    session.pop('profile_pic',None)
    session.pop('profile_pic_small',None)
    session.clear()
    return redirect(request.args.get('next'))

@app.route('/login/authorized')
@facebook.authorized_handler
@ndb.toplevel
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message

    session['oauth_token'] = (resp['access_token'], '')
    session['me'] = me = facebook.get('/me').data
    session['profile_pic'] = p_pic = facebook.get('me/picture?redirect=0&height=200&type=normal&width=200').data['data']['url']
    session['profile_pic_small'] = p_pic_s = facebook.get('me/picture?redirect=0&type=small').data['data']['url']
    if me.has_key('email'): 
        email = me['email']
        user = new.User(parent = ndb.Key("User", "user_table"),
                        id = email,
                        name = me['name'],
                        first_name = me['first_name'],
                        last_name = me['last_name'],
                        email = email,
                        pro_pic = p_pic,
                        pro_pic_small = p_pic_s,
                        from_ = 'facebook.com')
    user.put_async()
    return redirect(request.args.get('next'))

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def page_not_found(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
