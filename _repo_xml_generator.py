""" 
    Put this script in the root folder of your repo and it will
    zip up all addon folders, create a new zip in your zips folder
    and then update the md5 and addons.xml file
"""

import re
import os
import shutil
import hashlib
import zipfile
from xml.etree import ElementTree

class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
    """
    
    def __init__(self):
        self._remove_binaries()
        self._create_zips_folder()

        self._generate_addons_file()
        self._generate_md5_file()

    def _remove_binaries(self):
        """
            Removes any and all compiled Python files before operations.
        """
    
        for parent, dirnames, filenames in os.walk('.'):
            for fn in filenames:
                if fn.lower().endswith('pyo') or fn.lower().endswith('pyc'):
                    compiled = os.path.join(parent, fn)
                    try:
                        os.remove(compiled)
                        print("Removed compiled python file:")
                        print(compiled)
                        print('-----------------------------')
                    except:
                        print("Failed to remove compiled python file:")
                        print(compiled)
                        print('-----------------------------')
            for dir in dirnames:
                if "pycache" in dir.lower():
                    compiled = os.path.join(parent, dir)
                    try:
                        shutil.rmtree(compiled)
                        print("Removed __pycache__ cache folder:")
                        print(compiled)
                        print('-----------------------------')
                    except:
                        print("Failed to remove __pycache__ cache folder:")
                        print(compiled)
                        print('-----------------------------')

    def _create_zips_folder(self):
        """
            Creates a folder called 'zips', if it doesn't exist already.
            This folder is used to house the repo contents. 
        """
        
        zips_path = ('zips')
        if not os.path.exists(zips_path):
            os.makedirs(zips_path)    

    def _create_zip(self, addon_id, version):
        """
            Creates a zip file in the zips directory for the given addon.
        """
        addon_folder = os.path.join('zips', addon_id)
        if not os.path.exists(addon_folder):
            os.makedirs(addon_folder)

        final_zip = os.path.join('zips', addon_id, '{0}-{1}.zip'.format(addon_id, version))
        if not os.path.exists(final_zip):
            print("CREATING ZIP FOR: {0} - version={1}".format(addon_id, version))
            zip = zipfile.ZipFile(final_zip, 'w', compression=zipfile.ZIP_DEFLATED )
            root_len = len(os.path.dirname(os.path.abspath(addon_id)))
            
            ignore = ['.git', '.github', '.gitignore', '.DS_Store', 'thumbs.db', '.idea', 'venv']
            
            for root, dirs, files in os.walk(addon_id):
                # remove any unneeded artifacts
                for i in ignore:
                    if i in dirs:
                        try:
                            dirs.remove(i)
                        except:
                            pass
                    for f in files:
                        if f.startswith(i):
                            try:
                                files.remove(f)
                            except:
                                pass
                
                archive_root = os.path.abspath(root)[root_len:]

                for f in files:
                    fullpath = os.path.join(root, f)
                    archive_name = os.path.join(archive_root, f)
                    zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
            
            zip.close()
            
        self._copy_meta_files(addon_id, addon_folder)
            
                    
    def _copy_meta_files(self, addon_id, addon_folder):
        """
            Copy the addon.xml and relevant art files into the relevant folders in the repository.
        """

        tree = ElementTree.parse(os.path.join(addon_id, 'addon.xml'))
        root = tree.getroot()
        
        copyfiles = ['addon.xml']
        for ext in root.findall('extension'):
            if ext.get('point') == 'xbmc.addon.metadata':
                assets = ext.find('assets')
                for art in assets:
                    copyfiles.append(os.path.normpath(art.text))

        for file in copyfiles:
            addon_path = os.path.join(addon_id, file)
            zips_path = os.path.join(addon_folder, file)
            asset_path = os.path.split(zips_path)[0] 
            if not os.path.exists(asset_path):
                os.makedirs(asset_path)
            shutil.copy(addon_path, zips_path)

    def _generate_addons_file(self):
        """
            Generates a zip for each found addon, and updates the addons.xml file accordingly.
        """
        addons_xml = u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<addons>\n"

        for addon in [i for i in os.listdir('.') if os.path.isdir(i)
                                                 and i != 'zips'
                                                 and not i.startswith('.')
                                                 and os.path.exists(os.path.join(i, 'addon.xml'))]:
            try:
                _path = os.path.join(addon, "addon.xml")
                if not os.path.isdir(addon) or addon == "zips" or addon.startswith('.') or not os.path.exists(_path):
                    continue
                xml_lines = open(_path, "r", encoding='utf-8').read().splitlines()
                addon_xml = ""

                # loop thru cleaning each line
                ver_found = False
                for line in xml_lines:
                    if line.find( "<?xml" ) >= 0:
                        continue
                    if 'version="' in line and not ver_found:
                        version = re.compile('version="(.+?)"').findall(line)[0]
                        ver_found = True
                    addon_xml += line.rstrip() + "\n"
                addons_xml += addon_xml.rstrip() + "\n\n"

                # Create the zip files                
                self._create_zip(addon, version)

            except Exception as e:
                print("Excluding {0}: {1}".format(_path, e))

        # clean and add closing tag
        addons_xml = addons_xml.strip() + u"\n</addons>\n"
        self._save_file(addons_xml.encode('utf-8'), file=os.path.join('zips', 'addons.xml'), decode=True)
        print("Successfully updated addons.xml")

    def _generate_md5_file(self):
        """
            Generates a new addons.xml.md5 file.
        """
        try:
            m = hashlib.md5(open(os.path.join('zips', 'addons.xml'), 'r', encoding='utf-8').read().encode('utf-8')).hexdigest()
            self._save_file(m, file=os.path.join('zips', 'addons.xml.md5'))
            print("Successfully updated addons.xml.md5")
        except Exception as e:
            print("An error occurred creating addons.xml.md5 file!\n{0}".format(e))

    def _save_file(self, data, file, decode=False):
        """
            Saves a file.
        """
        try:
            if decode:
                open(file, 'w', encoding='utf-8').write(data.decode('utf-8'))
            else:
                open(file, 'w').write(data)
        except Exception as e:
            print("An error occurred saving {0} file!\n{1}".format(file, e))


if __name__ == "__main__":
    Generator()
