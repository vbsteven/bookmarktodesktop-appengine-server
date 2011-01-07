from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from xml.sax import saxutils
from google.appengine.api import channel
import datetime
import os
import md5

## Entities ##

class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    date = db.DateTimeProperty()

class Bookmark(db.Model):
    user = db.ReferenceProperty(User)
    url = db.StringProperty()
    title = db.StringProperty()
    fetched = db.BooleanProperty()
    date = db.DateTimeProperty()

## Utility methods ##

def usernameAvailable(username):
    users = db.GqlQuery("SELECT * FROM User WHERE username = :1", username)
    if users is None:
        return True
    if users.count() == 0:
        return True
    return False

def calculateHash(username, password):
    return md5.new(username+":"+password).hexdigest()
    
def checkLogin(username=None, password=None):
    password = calculateHash(username, password)
    
    if username is None:
        return None
    if username == '':
        return None
    if password is None:
        return None
    if password == '':
        return None
    
    users = db.GqlQuery("SELECT * FROM User WHERE username = :1 AND password = :2", username, password)
    if users is None:
        return None
    if users.count() <= 0:
        return None
    
    return users[0]

## Pages ##

# does nothing more than showing a text string
class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Bookmark to Desktop app')

# creates a new user
class CreateUser(webapp.RequestHandler):
    
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        
        username = self.request.get('username')
        password = self.request.get('password')
        if username is not None and username is not '':
            if not usernameAvailable(username):
                self.response.out.write('USERNAMEUNAVAILABLE')
                return
            if password is not None:
                password = calculateHash(username, password)
                user = User()
                user.username = username
                user.password = password
                user.date = datetime.datetime.utcnow()
                user.put()

                self.response.out.write('SUCCESSFUL')
                return
        self.response.out.write('INVALIDINPUT')
        return

# adds a new bookmark for a given user
class AddBookmark(webapp.RequestHandler):
    
    def get(self):
        return self.post()
    
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        username = self.request.get('username')
        password = self.request.get('password')
        url = self.request.get('url')
        title = self.request.get('title')
        
        user = checkLogin(username, password)
        if user is None:
            self.response.out.write('INVALIDLOGIN')
            return
        if url is None:
            self.response.out.write('INVALIDENTRY')
            return
        if url == '':
            self.response.out.write('INVALIDENTRY')
            return
        
        bookmark = Bookmark()
        bookmark.fetched = False
        bookmark.user = user
        bookmark.url = url
        bookmark.date = datetime.datetime.utcnow()
        bookmark.title = ''
        
        if title is not None:
            if title != '':
                bookmark.title = title
        
        bookmark.put()
        
        body = '{bookmark: {title:\'' + saxutils.escape(bookmark.title) + '\', url:\'' + saxutils.escape(bookmark.url) + '\'}}'
        channel.send_message(user.username, body)
        
        self.response.out.write('SUCCESSFUL')
        return

# returns not shared bookmarks for the given user
class FetchBookmarks(webapp.RequestHandler):
        def get(self):
            self.response.headers['Content-Type'] = 'text/xml'
            username = self.request.get('username')
            password = self.request.get('password')
            
            user = checkLogin(username, password)
            if user is None:
                self.response.out.write('INVALIDLOGIN')
                return
            
            bookmarks = db.GqlQuery("SELECT * FROM Bookmark WHERE user = :1 AND fetched = :2", user, False)
            
            xml = '<?xml version="1.0" ?><bookmarks>'
            for bookmark in bookmarks:
                if bookmark.title is None:
                    bookmark.title = ''
                xml += '<bookmark><url>' + saxutils.escape(bookmark.url) + '</url><title>' + saxutils.escape(bookmark.title) + '</title></bookmark>'
                bookmark.fetched = True
                bookmark.put()
            xml += '</bookmarks>'
            self.response.out.write(xml)

# logincheck used in the android app
class CheckLogin(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/html'
        username = self.request.get('username')
        password = self.request.get('password')

        user = checkLogin(username, password)
        if user is None:
            self.response.out.write('INVALIDLOGIN')
            return
        else:
            self.response.out.write('SUCCESS')
            return

# returns the channel token used for PUSH
class RequestToken(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        username = self.request.get('username')
        password = self.request.get('password')
            
        user = checkLogin(username, password)
        if user is None:
            self.response.out.write('INVALIDLOGIN')
            return
        self.response.out.write(channel.create_channel(user.username))	
        return

# shows html template for the addon/extension links
class Addons(webapp.RequestHandler):
    def get(self):
        template_values = {
	            'value': 1, }

        path = os.path.join(os.path.dirname(__file__), 'addons.html')
        self.response.out.write(template.render(path, template_values))



application = webapp.WSGIApplication([('/', MainPage),
                                      ('/createuser', CreateUser),
                                      ('/addbookmark', AddBookmark),
                                      ('/fetchbookmarks', FetchBookmarks),
				                      ('/requesttoken', RequestToken),
				                      ('/checklogin', CheckLogin),
				                      ('/addons', Addons),
                                      ], debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()