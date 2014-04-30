from main import app, requires_auth
from flask import g, session, request, redirect \
                  , render_template, render_template_string, Markup \
                  , flash, url_for, abort, escape \
                  , jsonify

from google.appengine.ext import ndb
from shorts import Shorts				  

from datetime import datetime, timedelta

import gdata.youtube
import gdata.youtube.service

class YT_crawler_temp(ndb.Model):
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

    @classmethod
    def query_all(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.v_rating,-cls.v_cnt)


def EntryDetailsDict(entry):
  alt_fmt_ = ""
  for alternate_format in entry.media.content:
    if 'isDefault' not in alternate_format.extension_attributes:
        alt_fmt_ = '%s | %s' % (alternate_format.type,
                                    alternate_format.url)
  if entry.rating:
	v_rating = float(entry.rating.average)
  else: v_rating = 0
  return dict(
      id = entry.id.text.split('/')[-1],
      title_ = entry.media.title.text,
      pub_on = datetime.strptime(entry.published.text[:18],"%Y-%m-%dT%H:%M:%S"),
      desc_ = entry.media.description.text,
      cat_ = entry.media.category[0].text,
      tags_ = entry.media.keywords.text,
      w_url = entry.media.player.url,
      f_url = entry.GetSwfUrl(),
      duration = int(entry.media.duration.seconds),
      v_cnt = int(entry.statistics.view_count),
      v_rating = v_rating,
      alt_fmt_ = alt_fmt_,
      th_nail_url = entry.media.thumbnail[0].url
      )

def InsertVideoFeedDataStore(feed):
  for entry in feed.entry:
    dump = YT_crawler_temp(parent= ndb.Key("YT_crawler_temp","youtube_crawler"),
                           **EntryDetailsDict(entry))
    dump.put_async()

def yt_search_and_store(search_terms):
  yt_service = gdata.youtube.service.YouTubeService()
  query = gdata.youtube.service.YouTubeVideoQuery()
  query.vq = search_terms
  query.orderby = 'viewCount'
  query.racy = 'include'
  feed = yt_service.YouTubeQuery(query)
  InsertVideoFeedDataStore(feed)
  return

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
		</ul><br><br><br><br>
		<form action="/crawler/youtube/delete" method="post">
		<input type="hidden" value="{id}" name="id">
		<button type="submit" class="btn btn-default btn-sm">
			<span class="glyphicon glyphicon-trash"></span>&nbsp;&nbsp;&nbsp;Delete it
		</button>
		</form>
		<form action="/shorts/add_short" method="post">
		<input type="hidden" value="{id}" name="id">
		<button type="submit" class="btn btn-default btn-sm">
			<span class="glyphicon glyphicon-plus"></span>&nbsp;Add to Shorts
		</button>
		</form>
	  </div>
	</div>
</li>
'''

@app.route("/crawler/youtube/list/")  
@app.route("/crawler/youtube/list/<int:limit>")
@app.route("/crawler/youtube/list/<int:strt>-<int:end>")
@ndb.toplevel
#@requires_auth
def yt_list_temp(limit=10, **kwargs):
	if request.args.get('search',None):
		yt_search_and_store(request.args.get('search',None))
	if kwargs.has_key('strt') and kwargs.has_key('end'):
		strt = kwargs['strt'] -1
		end = kwargs['end']
		dumps = YT_crawler_temp.query_all(ndb.Key("YT_crawler_temp", "youtube_crawler")).fetch()[strt:end]
	else: dumps = YT_crawler_temp.query_all(ndb.Key("YT_crawler_temp", "youtube_crawler")).fetch(limit)
	if request.args.get('knockout',None):
		return jsonify({'shorts':[{'id':s.key.id(),'details':s.to_dict(),'d_hhmmss':str(timedelta(seconds=s.duration))} for s in dumps]})
	dumps = [ yt_entry.format(title=s.title_,id=s.key.id(),rating=s.v_rating,v_cnt=s.v_cnt,duration=str(timedelta(seconds=s.duration))) for s in dumps ]
#	dumps = [ '<li>'+s.title_+'<br>'+yt_thumb_s%(s.w_url,s.title_,s.th_nail_url,s.key.id())+'<br>\n' for s in dumps ]
	return render_template("yt_crawl_ko.html",title="YouTube Crawl Temp")
	
  
@app.route("/crawler/youtube/delete", methods=['POST','GET'])
#@requires_auth
def yt_delete_from_temp():
	id = request.form.get('id',None) or request.args.get('id',None)
	if id:
		k_ = ndb.Key("YT_crawler_temp", "youtube_crawler","YT_crawler_temp",id)
		k_.delete()
	return jsonify(dict(delete=True))
	