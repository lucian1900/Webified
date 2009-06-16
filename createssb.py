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

def change_info(path, name, bundle_id):
    config = ConfigParser()
    config.read(path)

    if config.get('Activity', 'name') == 'Browse':
        version = 1
    else:
        version = int(config.get('Activity', 'activity_version')) + 1

    config.set('Activity', 'activity_version', version)    
    config.set('Activity', 'name', name)
    config.set('Activity', 'bundle_id', bundle_id)

    # 'commit' the changes
    f = open(path, 'w')
    config.write(f)
    f.close()

def create(title, uri):
    name = title.replace(' ', '')

    # set up the needed paths
    bundle_path = activity.get_bundle_path()
    temp_path = tempfile.mkdtemp() # make sure there's no collisions
    ssb_path = os.path.join(temp_path, name + '.activity')

    # copy the entire bundle
    shutil.copytree(bundle_path, ssb_path)

    # change activity.info accordingly
    info_path = os.path.join(ssb_path, 'activity/activity.info')
    change_info(path=info_path, name=title, 
                bundle_id='%s.%sActivity' % (DOMAIN_PREFIX, name))
    
    # set homepage
    f = open(os.path.join(ssb_path, 'data/homepage'), 'w')
    f.write(uri)
    f.close()

    # HACK: just delete the locale, it's only needed for the activity name
    #shutil.rmtree(os.path.join(ssb_path,'locale'))

    # create MANIFEST
    files = bb.list_files(ssb_path, ignore_dirs=bb.IGNORE_DIRS, 
                       ignore_files=bb.IGNORE_FILES)

    f = open(os.path.join(ssb_path, 'MANIFEST'), 'w')
    for i in files:
        f.write(i+'\n')
    f.close()

    # create .xo
    # include the manifest
    files.append('MANIFEST')

    xo_path = os.path.join(temp_path, name.lower() + '.xo')

    xo = zipfile.ZipFile(xo_path, 'w', zipfile.ZIP_DEFLATED)
    for i in files:
        xo.write(os.path.join(ssb_path, i), 
                 os.path.join( name + '.activity', i))
    xo.close()
    
    # install the xo
    # TODO investigate offering 'download' link for the .xo
    bundle = ActivityBundle(xo_path)
    bundle.install()

    # clean up tmp dir
    shutil.rmtree(temp_path)
