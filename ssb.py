# Copyright (C) 2009, Lucian Branescu Mihaila
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from sugar.activity import activity
from sugar.datastore import datastore
from sugar.activity import bundlebuilder as bb
from sugar.bundle.activitybundle import ActivityBundle
from sugar import profile
# how about sugar.util.list_files ?

import ConfigParser
import shutil
import os
import tempfile
import zipfile
import logging

DOMAIN_PREFIX = 'org.sugarlabs.ssb'

class SSBCreator(object):
    def __init__(self, title, uri):
        self.title = title
        self.name = title.replace(' ', '')
        self.uri = uri
        
        self.bundle_id = '%s.%sActivity' % (DOMAIN_PREFIX, self.name)
        logging.debug('bundle_id: ' + self.bundle_id)
        
        self.setup()
        
    def __del__(self):
        '''clean up after ourselves'''
        shutil.rmtree(temp_path)
        
    def setup(self):
        '''create tmp dir, setup paths, copy activity files'''
        self.bundle_path = activity.get_bundle_path()
        self.temp_path = tempfile.mkdtemp() # make sure there's no collisions
        self.ssb_path = os.path.join(self.temp_path, self.name + '.activity')
        
        # copy the entire bundle
        shutil.copytree(self.bundle_path, self.ssb_path)
        
    def change_info(self):
        '''change the .info file accordingly'''
        path = os.path.join(self.ssb_path, 'activity/activity.info')
        
        config = ConfigParser.RawConfigParser()
        config.read(path)

        if config.get('Activity', 'name') == 'Browse':
            version = 1
        else:
            version = int(config.get('Activity', 'activity_version')) + 1

        config.set('Activity', 'activity_version', version)    
        config.set('Activity', 'name', self.title)
        config.set('Activity', 'bundle_id', self.bundle_id)

        # 'commit' the changes
        f = open(path, 'w')
        config.write(f)
        f.close()
        
    def create(self):
        self.change_info()
        
        # set homepage
        f = open(os.path.join(self.ssb_path, 'data/homepage'), 'w')
        f.write(self.uri)
        f.close()

        # create MANIFEST
        files = bb.list_files(self.ssb_path, ignore_dirs=bb.IGNORE_DIRS, 
                              ignore_files=bb.IGNORE_FILES)

        f = open(os.path.join(self.ssb_path, 'MANIFEST'), 'w')
        for i in files:
            f.write(i+'\n')
        f.close()

        # create .xo
        # include the manifest
        files.append('MANIFEST')

        self.xo_path = os.path.join(self.temp_path, self.name.lower() + '.xo')

        # zip everything
        xo = zipfile.ZipFile(self.xo_path, 'w', zipfile.ZIP_DEFLATED)
        for i in files:
            xo.write(os.path.join(self.ssb_path, i), 
                     os.path.join(self.name + '.activity', i))
        xo.close()
        
        logging.debug('.xo bundle path: ' + self.xo_path)

    def install(self):
        '''install the generated .xo bundle'''
        bundle = ActivityBundle(self.xo_path)
        bundle.install()
        
    def send_to_journal(self):
        '''send the generated .xo bundle to the journal'''
        # TODO: investigate sending the .xo to the journal
        jobject = datastore.create()
        jobject.metadata['title'] = self.title
        jobject.metadata['mime_type'] = 'application/vnd.olpc-sugar'
        jobject.metadata['icon-color'] = profile.get_color().to_string()
        jobject.file_path = self.xo_path
        datastore.write(jobject)
