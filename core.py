from __future__ import print_function
import os
import re
import sys
import cPickle
import hashlib
import mimetypes
import uuid
from PIL import Image as PILImage
from PIL import ExifTags as PILExifTags

from hw import utils

mimetypes.init()
__version__ = '0.0.1'

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class GalleryEntity(object):
    def __init__(self, database_root_dir):
        self._v_database_root_dir_ = database_root_dir

class FileEntity(object):
    """Class describing a physical file on disc. Used as a handle
    in the database.

    """
    def __init__(self, image_root_dir, relpathfilename):
        """Creates a new file entity for the given file. It creates a sha1
        checksum of the file.

        """
        # Create a random uuid for this entity.
        pathfilename = os.path.join(image_root_dir, relpathfilename)
        self._v_uuid_ = uuid.uuid4()
        self._v_relpathfilename_ = relpathfilename
        self._v_mimetype_ = mimetypes.guess_type(pathfilename, strict=False)
        f = open(pathfilename, 'r')
        self._v_sha1_hash_ = hashlib.sha1(f.read()).hexdigest()
        f.close()
        self._v_tags_list_ = list()

class ImageFileEntity(FileEntity):
    """Describes a physical image file on disc.

    """
    def __init__(self, image_root_dir, relpathfilename):
        super(ImageFileEntity, self).__init__(image_root_dir, relpathfilename)
        pathfilename = os.path.join(image_root_dir, relpathfilename)
        img = PILImage.open(pathfilename)
        exifdata = img._getexif()
        if(exifdata is None):
            self._v_exif_dict_ = dict()
        else:
            self._v_exif_dict_ = {
                PILExifTags.TAGS[k]: v for k, v in exifdata.items()
                                       if k in PILExifTags.TAGS
            }


class HierachyNode(AttrDict):
    """Provides a node object for the hierachy. Each node has one parent node
    and can have several child nodes.

    """
    def __init__(self, name, title):
        super(HierachyNode, self).__init__()
        self._v_name_ = name
        self._v_title_ = title

    def add_node(self, name, title):
        self[name] = HierachyNode(name, title)
        return self[name]

    def delete_node(self, name):
        del(self[name])

class GalleryDatabase(object):
    def __init__(self,
        image_root_dir
      , image_path_pattern_list
      , image_fext_pattern_list
    ):
        self._v_image_root_dir_ = image_root_dir
        self._v_image_path_pattern_list_ = image_path_pattern_list
        self._v_image_fext_pattern_list_ = image_fext_pattern_list
        self._v_root_node_ = HierachyNode('root', '')
        self._v_file_entity_dict_ = dict()

    def _get_root(self):
        return self._v_root_node_
    root = property(fget=_get_root, doc='The root node.')

    def _add_file_entity(self, fe):
        """Adds the given file entity object to the database.

        """
        self._v_file_entity_dict_[fe._v_uuid_] = fe

    def _delete_file_entity(self, fe):
        """Deletes the given file entity object from the database.

        """
        del(self._v_file_entity_dict_[fe._v_uuid_])

    def _content_exists(self, fe):
        """Checks if the content, describes by the given file entity already
        exists in the database. When yes, returns the already
        existing file entity. When no, returns ``False``.

        """
        for (uuid, fentity) in self._v_file_entity_dict_.iteritems():
            if(fentity._v_sha1_hash_ == fe._v_sha1_hash_):
                return fentity
        return False




class HWUI(object):
    """The user interface class providing all user space functions.

    """
    _v_gallery_entity_dict_ = AttrDict()
    galls = _v_gallery_entity_dict_
    _v_gallery_database_dict_ = AttrDict()
    dbs = _v_gallery_database_dict_

    def __init__(self, config_dir):
        # Check if the config directory exists, and if not, create it.
        if(not os.path.exists(config_dir)):
            os.makedirs(config_dir)
        galleries_dir = os.path.join(config_dir, 'galleries')
        if(not os.path.exists(galleries_dir)):
            os.makedirs(galleries_dir)
        self._v_config_dir_ = config_dir
        self._v_galleries_dir_ = galleries_dir

        # Load all the available gallery entities and their databases.
        fnames = os.listdir(self._v_galleries_dir_)
        for fname in fnames:
            if(fname[-8:] != '.hwgalle'):
                continue
            f = open(os.path.join(self._v_galleries_dir_, fname), 'r')
            gallentity = cPickle.load(f)
            f.close()
            gallentity_name = fname[0:-8]
            self._f_register_gallery_entity(gallentity, gallentity_name)

            f = open(os.path.join(gallentity._v_database_root_dir_, 'db.hwdb'), 'r')
            galldb = cPickle.load(f)
            f.close()
            self._f_register_gallery_database(galldb, gallentity_name)

    def __del__(self):
        # Save the changes of all the gallery entities and databases.
        self.save()

    def save(self):
        """Saves all the data to disc.

        """
        for (gallentity_name, gallentity) in self._v_gallery_entity_dict_.iteritems():
            gallentity_fn = os.path.join(self._v_galleries_dir_, gallentity_name+'.hwgalle')
            f = open(gallentity_fn, 'w')
            cPickle.dump(gallentity, f)
            f.close()
            print('Gallery entity stored in "%s".'%(gallentity_fn))

            galldb = self._v_gallery_database_dict_[gallentity_name]
            galldb_fn = os.path.join(gallentity._v_database_root_dir_, 'db.hwdb')
            f = open(galldb_fn, 'w')
            cPickle.dump(galldb, f)
            f.close()
            print('Gallery database stored in "%s".'%(galldb_fn))

    def _f_register_gallery_entity(self, gallentity, gallentity_name):
        """Registers the given gallery entity as the given name to this user
        interface.

        """
        self._v_gallery_entity_dict_[gallentity_name] = gallentity
        print('Added gallery entity "%s" to galls property.'%(gallentity_name))

    def _f_register_gallery_database(self, galldb, gallentity_name):
        """Registers the given gallery database as the given name to this user
        interface.

        """
        self._v_gallery_database_dict_[gallentity_name] = galldb
        print('Added gallery database "%s" to dbs property.'%(gallentity_name))

    def create_gallery(self):
        """Creates a new gallery by creating a new gallery entity and gallery
        database by asking the user about their locations and extra information.
        The gallery entity is stored in the config directory and the database
        at the user specified location.

        """
        image_root_dir = utils.get_path_from_user(
            'Image root directory?'
           , os.path.expanduser(os.path.join('~', 'Pictures'))
           , 'exists')

        print('')
        gallentity_name = utils.get_string_from_user(
            'Name of the gallery entity?'
           , utils.attributeize(os.path.basename(image_root_dir)))
        gallentity_name = utils.attributeize(gallentity_name)

        print('')
        database_root_dir = utils.get_path_from_user(
            'Gallery database root directory?'
          , os.path.expanduser(os.path.join(image_root_dir, '.hwdb'))
          , 'create_if_not_exists')

        print('')
        print('What image pathes should get recognized when searching\n'+\
              'for image files? The default is all pathes below the image\n'+\
              'root directory.')
        image_path_pattern_list = utils.get_string_list_from_user(
            'Image path pattern?'
          , r'.+'
          , chr(27))

        print('')
        print('What image file extension should get recognized when searching ')
        print('for image files?')
        image_fext_pattern_list = list()
        if(utils.get_yesno_from_user('Recognize JPEG images?', 'y')):
            image_fext_pattern_list.append(r'\.[jJ][pP][gG]$')
            image_fext_pattern_list.append(r'\.[jJ][pP][eE][gG]$')
        if(not utils.get_yesno_from_user('Recognize PNG images?', 'n')):
            image_fext_pattern_list.append(r'\.[pP][nN][gG]$')

        # Summarize user information.
        print('')
        print('='*80)
        print('Gathering of user information completed.')
        print('-'*80)
        print('Taking "%s" as image root directory.'%(image_root_dir))
        print('Taking "%s" as gallery entity name.'%(gallentity_name))
        print('Taking "%s" as gallery database root directory.'%(database_root_dir))
        print('-'*80)
        if(not utils.get_yesno_from_user('Is this all correct?', 'y')):
            print('Aborting ...')
            return

        # Create the gallery entity object.
        gallentity = GalleryEntity(database_root_dir)
        self._f_register_gallery_entity(gallentity, gallentity_name)

        # Create the database object.
        galldb = GalleryDatabase(
            image_root_dir
          , image_path_pattern_list
          , image_fext_pattern_list)
        self._f_register_gallery_database(galldb, gallentity_name)

    def _accept_file(self, galldb, path, fname):
        """Checks if the given file is accepted by the database.

        """
        # Check if the path matches any path patterns.
        path_accepted = False
        for pattern in galldb._v_image_path_pattern_list_:
            if(re.search(pattern, path) is not None):
                path_accepted = True
                break

        # Check if the filename extension matches any filename extension
        # patterns.
        fext_accepted = False
        for pattern in galldb._v_image_fext_pattern_list_:
            if(re.search(pattern, fname) is not None):
                fext_accepted = True
                break

        return (path_accepted and fext_accepted)

    def sync_gallery_db(self, galldb, subpath=None):
        """Syncronizes the given gallery database with the physical image files
        by looking for new or updated files.
        If subpath is given, the syncronization starts at the specified sub
        path, instead of the image root directory.

        """
        root_dir = galldb._v_image_root_dir_
        if(subpath is not None):
            root_dir = os.path.join(root_dir, subpath)

        # Check for new or moved files.
        for (path, dnames, fnames) in os.walk(root_dir, topdown=True, followlinks=False):
            # Cut the root dir.
            path = path[len(root_dir)+len(os.sep):]
            for fname in fnames:
                # Check if the filename is accepted by the database.
                if(not self._accept_file(galldb, path, fname)):
                    continue

                # Automatically determine tags from the file location.
                # TODO

                # Get the mime type and create the file entity.
                pathfilename = os.path.join(root_dir, path, fname)
                relpathfilename = pathfilename[len(galldb._v_image_root_dir_)+len(os.sep):]
                print('root_dir = %s'%root_dir)
                print('_v_image_root_dir_ = %s'%(galldb._v_image_root_dir_))
                print('pathfilename = %s'%pathfilename)
                print('relpathfilename = %s'%relpathfilename)
                mt = mimetypes.guess_type(pathfilename, strict=False)[0]
                if((mt is not None) and (mt[0:5] == 'image')):
                    fe = ImageFileEntity(galldb._v_image_root_dir_, relpathfilename)
                else:
                    fe = FileEntity(galldb._v_image_root_dir_, relpathfilename)

                # Check if the file already exists in the database.
                fedb = galldb._content_exists(fe)
                if(fedb):
                    # Check if the file location has changed.
                    if(fedb._v_relpathfilename_ != fe._v_relpathfilename_):
                        print('It seems that the file "%s" has physically moved to "%s".'%(
                            fedb._v_relpathfilename_, fe._v_relpathfilename_))
                        if(utils.get_yesno_from_user('Update database accordingly?', 'y')):
                            fedb._v_relpathfilename_ = fe._v_relpathfilename_
                else:
                    galldb._add_file_entity(fe)

        # Check for deleted files.
        for (uuid, fe) in galldb._v_file_entity_dict_.iteritems():
            pathfilename = os.path.join(galldb._v_image_root_dir_, fe._v_relpathfilename_)
            if(not pathfilename.startswith(root_dir)):
                continue
            if(not os.path.exists(pathfilename)):
                print('The file "%s" does not exist anymore.'%(pathfilename))
                if(utils.get_yesno_from_user('Delete file entity from database?', 'y')):
                    galldb._delete_file_entity(fe)
