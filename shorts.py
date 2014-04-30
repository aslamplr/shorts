import logging
from main import app, requires_auth
from flask import g, session, request, redirect \
                  , render_template, render_template_string, Markup \
                  , flash, url_for, abort, escape \
                  , jsonify

from google.appengine.ext import ndb

from datetime import datetime, timedelta

class Shorts(ndb.Model):
    title_ = ndb.StringProperty()
    pub_on = ndb.DateTimeProperty()
    desc_ = ndb.StringProperty()
    cat_ = ndb.StringProperty()
    tags_ = ndb.StringProperty()
    w_url = ndb.StringProperty()
    f_url = ndb.StringProperty()
    duration = ndb.IntegerProperty()
    v_cnt = ndb.IntegerProperty()
    v_rating = ndb.FloatProperty()
    alt_fmt_ = ndb.StringProperty()
    th_nail_url = ndb.StringProperty()
    src = ndb.StringProperty()

    @classmethod
    def query_all(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.pub_on,-cls.v_rating,-cls.v_cnt)

@ndb.transactional(xg=True,retries=2)
def del_from_tmp_insrt_shorts(id,tags):
	k_ = ndb.Key("YT_crawler_temp", "youtube_crawler","YT_crawler_temp",id)
	d_ = k_.get().to_dict()
	if tags and d_['tags_']: d_['tags_'] = d_['tags_'] + tags
	elif tags: d_['tags_'] = tags
	_id = Shorts(parent=ndb.Key("Shorts","short_films"),
					id=id, src='youtube', **d_)
	_id.put()
	k_.delete()		
		
@app.route("/shorts/add_short",methods=['POST','GET'])
@ndb.toplevel
#@requires_auth
def add_short():
	id = request.form.get('id',None) or request.args.get('id',None)
	tags = request.form.get('tags',None) or request.args.get('tags',None)
	if id: 
		del_from_tmp_insrt_shorts(id,tags)
	return jsonify(dict(delete=True))

yt_entry = u'''
<li class="list-group-item">
	<div class="media">
	  <a class="pull-left" href="#">
		<iframe title="YouTube video player" class="youtube-player" type="text/html" 
			width="480" height="349" src="http://www.youtube.com/embed/{id}"
				frameborder="0" allowFullScreen></iframe>
	  </a>
	  <div class="media-body">
		<h4 class="media-heading">{title}</h4>
		<ul> 
			<li>Rating: {rating}
			<li>View Count: {v_cnt}
			<li>Duration: {duration}
		</ul>
	  </div>
	</div>
</li>
'''
	
@app.route("/shorts/list/")
@app.route("/shorts/list/<int:limit>")
@app.route("/shorts/list/<int:strt>-<int:end>")
def shorts_list(limit=10,**kwargs):
	#flash("A simple flash",'info')
	if kwargs.has_key('strt') and kwargs.has_key('end'):
		strt = kwargs['strt'] -1
		end = kwargs['end']
		dumps = dumps = Shorts.query_all(ndb.Key("Shorts", "short_films")).fetch()[strt:end]
	else: dumps = Shorts.query_all(ndb.Key("Shorts", "short_films")).fetch(limit)
	if request.args.get('knockout',None):
		return jsonify({'shorts':[{'id':s.key.id(),'details':s.to_dict(),'d_hhmmss':str(timedelta(seconds=s.duration))} for s in dumps]})
	dumps = [ yt_entry.format(title=s.title_,id=s.key.id(),rating=s.v_rating,v_cnt=s.v_cnt,duration=str(timedelta(seconds=s.duration))) for s in dumps ]
	return render_template("index.html",html_content='<ul class="list-group">'+"\n".join(dumps)+"</ul>\n<br><br><hr><br>",title="NDB")