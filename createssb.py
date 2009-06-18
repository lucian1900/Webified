from sugar.activity import activity
from sugar.activity import bundlebuilder as bb
from sugar.bundle.activitybundle import ActivityBundle
# how about sugar.util.list_files ?

from ConfigParser import ConfigParser
import shutil
import os
import tempfile
import zipfile

DOMAIN_PREFIX = 'org.sugarlabs.ssb'
    
class SSBCreator(object):
    def __init__(self, title, uri):
        self.title = title
        self.name = title.replace(' ', '')
        self.uri = uri
        
        self.bundle_id = '%s.%sActivity' % (DOMAIN_PREFIX, name)
        
        self.setup()
        
    def __del__(self):
        '''clean up after ourselves'''
        shutil.rmtree(temp_path)
        
    def setup(self):
        '''create tmp dir, setup paths, copy activity files'''
        self.bundle_path = activity.get_bundle_path()
        self.temp_path = tempfile.mkdtemp() # make sure there's no collisions
        self.ssb_path = os.path.join(temp_path, self.name + '.activity')
        
        # copy the entire bundle
        shutil.copytree(self.bundle_path, self.ssb_path)
        
    def change_info(self):
        '''change the .info file accordingly'''
        path = os.path.join(self.ssb_path, 'activity/activity.info')
        
        config = ConfigParser()
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

        f = open(os.path.join(ssb_path, 'MANIFEST'), 'w')
        for i in files:
            f.write(i+'\n')
        f.close()

        # create .xo
        # include the manifest
        files.append('MANIFEST')

        self.xo_path = os.path.join(self.temp_path, name.lower() + '.xo')

        xo = zipfile.ZipFile(self.xo_path, 'w', zipfile.ZIP_DEFLATED)
        for i in files:
            xo.write(os.path.join(ssb_path, i), 
                     os.path.join( name + '.activity', i))
        xo.close()

    def install(self):
        '''install the generated .xo bundle'''
        # TODO investigate offering 'download' link for the .xo
        bundle = ActivityBundle(self.xo_path)
        bundle.install()
