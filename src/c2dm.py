import urllib, urllib2

class C2DM():

    def __init__(self):
        self.url = 'http://android.apis.google.com/c2dm/send'
        self.clientAuth = None
        self.registrationId = None
        self.collapseKey = None
        self.data = {}

    def sendMessage(self, url):
        if self.registrationId == None or self.collapseKey == None:
            return False

        # Build payload
        values = {'registration_id' : self.registrationId,
          'collapse_key' : self.collapseKey,
          'data.url':url}

        # Build request
        headers = {'Authorization': 'GoogleLogin auth=' + self.clientAuth}
        data = urllib.urlencode(values)
        request = urllib2.Request(self.url, data, headers)

        # Post
        try:
            response = urllib2.urlopen(request)
            responseAsString = response.read()

            return responseAsString
        except urllib2.HTTPError, e:
            return 'HTTPError ' + str(e)



