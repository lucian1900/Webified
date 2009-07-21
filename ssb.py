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

import shutil
import os
import tempfile
import zipfile
import ConfigParser
import logging
from fnmatch import fnmatch

from sugar.activity import activity
from sugar.bundle.activitybundle import ActivityBundle
from sugar.datastore import datastore
from sugar import profile

DOMAIN_PREFIX = 'org.sugarlabs.ssb'

IGNORE_DIRS = ['dist', '.git']
IGNORE_FILES = ['.gitignore', 'MANIFEST', '*.pyc', '*~', '*.bak', 
                'pseudo.po', '.DS_STORE']

def get_is_ssb(activity):
    '''determine if the activity is an SSB'''
    return activity.get_bundle_id().startswith(DOMAIN_PREFIX)

def list_files(base_dir, ignore_dirs=None, ignore_files=None):
    result = []

    base_dir = os.path.abspath(base_dir)

    for root, dirs, files in os.walk(base_dir):
        if ignore_files:
            for pattern in ignore_files:
                files = [f for f in files if not fnmatch(f, pattern)]

        rel_path = root[len(base_dir) + 1:]
        for f in files:
            result.append(os.path.join(rel_path, f))

        if ignore_dirs and root == base_dir:
            for ignore in ignore_dirs:
                if ignore in dirs:
                    dirs.remove(ignore)

    return result

def remove_paths(paths, root=None):
    '''remove all paths in the list, fail silently'''
    if root is not None:
        paths = [os.path.join(root, i) for i in paths]
    
    for path in paths:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError:
            logging.warning('failed to remove: ' + path)

def copy_profile():
    '''get the data from the bundle and into the profile'''
    ssb_data_path = os.path.join(activity.get_bundle_path(), 'data/ssb_data')
    data_path = os.path.join(activity.get_activity_root(), 'data')

    if os.path.isdir(ssb_data_path):
        # we can't use shutil.copytree for the entire dir
        for i in os.listdir(ssb_data_path):
            src = os.path.join(ssb_data_path, i)
            dst = os.path.join(data_path, i)
            if not os.path.exists(dst):
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else: # is there a better way?
                    shutil.copy(src, dst)

class SSBCreator(object):
    def __init__(self, title, uri):
        self.title = title
        self.name = title.replace(' ', '')
        self.uri = uri
        self.bundle_id = '%s.%sActivity' % (DOMAIN_PREFIX, self.name)        
        
        self.bundle_path = activity.get_bundle_path()
        self.data_path = os.path.join(activity.get_activity_root(), 'data')
        self.temp_path = tempfile.mkdtemp() # make sure there's no collisions
        self.ssb_path = os.path.join(self.temp_path, self.name + '.activity')
        
    def __del__(self):
        '''clean up after ourselves, fail silently'''
        shutil.rmtree(self.temp_path, ignore_errors=True)
        
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
        config.set('Activity', 'icon', 'activity-ssb')

        # write the changes
        f = open(path, 'w')
        config.write(f)
        f.close()
        
    def create(self):
        '''actual creation'''
        # copy the bundle
        shutil.copytree(self.bundle_path, self.ssb_path)
        
        self.change_info()
        
        # add the ssb icon
        shutil.copy(os.path.join(self.ssb_path, 'icons/activity-ssb.svg'),
                    os.path.join(self.ssb_path, 'activity'))
        
        # set homepage
        f = open(os.path.join(self.ssb_path, 'data/homepage'), 'w')
        f.write(self.uri)
        f.close()

        # copy profile
        ssb_data_path = os.path.join(self.ssb_path, 'data/ssb_data')
        shutil.copytree(self.data_path, ssb_data_path)
                      
        # delete undesirable things from the profile
        remove_paths(['Cache', 'cookies.sqlite'],
                     root=os.path.join(ssb_data_path, 'gecko'))

        # create MANIFEST
        files = list_files(self.ssb_path, IGNORE_DIRS, IGNORE_FILES)
        f = open(os.path.join(self.ssb_path, 'MANIFEST'), 'w')
        for i in files:
            f.write(i+'\n')
        f.close()

        # create .xo bundle
        # include the manifest
        files.append('MANIFEST')

        self.xo_path = os.path.join(self.temp_path, self.name.lower() + '.xo')

        # zip everything
        xo = zipfile.ZipFile(self.xo_path, 'w', zipfile.ZIP_DEFLATED)
        for i in files:
            xo.write(os.path.join(self.ssb_path, i), 
                     os.path.join(self.name + '.activity', i))
        xo.close()
        
    def install(self):
        '''install the generated .xo bundle'''
        bundle = ActivityBundle(self.xo_path)
        bundle.install()
        
    def show_in_journal(self):
        '''send the generated .xo bundle to the journal'''
        jobject = datastore.create()
        jobject.metadata['title'] = self.title
        jobject.metadata['mime_type'] = 'application/vnd.olpc-sugar'
        jobject.metadata['icon-color'] = profile.get_color().to_string()
        jobject.file_path = self.xo_path
        
        datastore.write(jobject)
        
        activity.show_object_in_journal(jobject.object_id) 