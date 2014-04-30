from main import app, requires_auth
from flask import g, session, request, redirect \
                  , render_template, render_template_string, Markup \
                  , flash, url_for, abort, escape \
                  , jsonify

from google.appengine.ext import ndb				  

class User(ndb.Model):
	name = ndb.StringProperty('nam')
	first_name = ndb.StringProperty('fnam')
	last_name = ndb.StringProperty('lnam')
	email = ndb.StringProperty()
	pro_pic = ndb.StringProperty('pic')
	pro_pic_small = ndb.StringProperty('pic_s')
	from_ = ndb.StringProperty('frm_')
	ld_ts = ndb.DateTimeProperty(auto_now=True)
	
	@classmethod
	def query_user(cls, ancestor_key):
		return cls.query(ancestor=ancestor_key).order(-cls.ld_ts)

user_entry = '''
<div class="media list-group-item">
  <a class="pull-left" href="#">
    <img class="media-object" src="{pro_pic}" alt="{name}">
  </a>
  <div class="media-body">
    <h4 class="media-heading">{name}</h4>
    <a href="/user/{email}">{email}</a>
	<button type="button" class="btn btn-default btn-xs">
		<span class="glyphicon glyphicon-trash"></span>
	</button>
  </div>
</div>
'''
		
@app.route("/user_list/",methods=['GET','POST'])
@ndb.toplevel
def ndb_test():
	if request.method == 'GET':
		ancestor_key = ndb.Key("User", "user_table")
		users = User.query_user(ancestor_key).fetch(10)
		users = [ user_entry.format(pro_pic=user.pro_pic,name=user.name,email=user.email) for user in users ]
		#flash("Another flashed message",'success')
		#flash("Another flashed message",'info')
		#flash("Another flashed message",'warning')
		#flash("Another flashed message",'danger')
		return render_template("index.html",html_content="<br>".join(users)+"<br><br><hr><br>",title="NDB")
	elif request.method == 'POST':
		user_name = request.form.get("name",None)
		email = request.form.get("email",None)
		if user_name:
			user = User(parent = ndb.Key("User", "user_table"),
						id = email,
						name = user_name, email = email)
			key_ = user.put_async()
			u = ndb.Key("User", "user_table", "User", email).get()
			if u:
				assert u.email == email
		flash('User added with email - %s' %(email),'info')
		return redirect(url_for('ndb_test'))


@app.route("/user/<email>",methods=['GET','POST','DELETE'])
def user_query(email):
	if request.method == 'GET':
		user_key = ndb.Key("User", "user_table", "User", email)
		user = user_key.get()
		if user:
			return render_template("index.html",html_content="%s | %s <form action=\"/user/%s\" method=\"post\"><input type=\"submit\" value=\"Delete\"></form>"%(user.name,user.email,user.email)+"<br><br><hr><br>",title="NDB")
		return redirect(url_for('ndb_test'))
	elif request.method in ['POST','DELETE']:
		user_key = ndb.Key("User", "user_table", "User", email)
		user_key.delete()
		return redirect(url_for('ndb_test'))