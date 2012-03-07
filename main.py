#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from google.appengine.api import memcache, urlfetch

from xml.dom import minidom

MTA_URL = 'http://www.mta.info/status/serviceStatus.txt'
MEMCACHE_MTA_DATA_KEY = 'mta-data'

class MainHandler(webapp.RequestHandler):
    def query_mta_service(self):
        url = MTA_URL
        result = urlfetch.fetch(url)
        
        if result.status_code == 200:
            return result.content
        else:
            return None
    
    def get_mta_data(self):
        xml_data = memcache.get(MEMCACHE_MTA_DATA_KEY)
        
        if not xml_data:
            xml_data = self.query_mta_service()
            memcache.set(MEMCACHE_MTA_DATA_KEY, xml_data, 1 * 60)
            
        return xml_data
    
    def get(self):
        self.response.headers['Cache-Control'] = 'public, max-age:300'
        
        xml_data = self.get_mta_data()
        dom_data = minidom.parseString(xml_data)
        
        statuses = []
        
        for line in dom_data.getElementsByTagName('subway')[0].getElementsByTagName('line'):
            name = line.getElementsByTagName('name')[0].childNodes[0].data
            status = line.getElementsByTagName('status')[0].childNodes[0].data
            if name != 'SIR':
                statuses.append({'name': name, 'status': status, 'individuals': list(name)})
                    

        values = {'lines': statuses}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, values))


def main():
    application = webapp.WSGIApplication([('/', MainHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
