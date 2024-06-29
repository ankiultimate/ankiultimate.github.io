# -*- coding: utf-8 -*-
# Copyright [2024] [random9528]

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import hashlib
import json
import os
import platform
import sys
import urllib
import zipfile
from pathlib import Path


def get_absolute_path(file):
    addon_path = os.path.dirname(__file__)
    return os.path.join(addon_path, file)


def get_identify():
    op_system = platform.system()
    return ''.join(platform.python_version_tuple()[0:2]) + '-' + op_system + '-' + platform.machine()


def download_file(remote_url, local_path):
    real_name = os.path.basename(local_path)
    urllib.request.urlretrieve(remote_url, local_path)
    if "__init__.py" == real_name:
        import aqt
        aqt.utils.showWarning('Ultimate Addon has been updated, please restart Anki')


def get_latest_info():
    remote_url = 'https://ankiultimate.github.io/main.json'
    req = urllib.request.Request(remote_url)
    req.add_header('User-Agent', 'ultimate-addon-client')
    response = urllib.request.urlopen(req, None, timeout=5)
    resp_content = response.read().decode()
    return json.loads(resp_content)


def merge_config(original, update):
    for key in original.keys():
        value = original[key]
        if key not in update:
            update[key] = value
        elif isinstance(value, dict):
            merge_config(value, update[key])
    return update


def compare_and_download_files(base_folder, files):
    for _file in files:
        full_path = os.path.join(base_folder, _file['file'])
        if os.path.isfile(full_path):
            hash = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
            if hash != _file['hash']:
                download_file(_file['url'], full_path)
                if _file['file'] == 'config.json':
                    meta_path = os.path.join(base_folder, "meta.json")
                    meta_config = {}
                    if Path(meta_path).exists():
                        with open(meta_path, 'rb') as file:
                            content = file.read()
                            meta_config = json.loads(content)
                            if "config" in meta_config:
                                meta_config = meta_config["config"]
                    with open(full_path, 'rb') as file:
                        content = file.read()
                        main_config = json.loads(content)
                    merged_config = merge_config(main_config, meta_config)
                    with open(meta_path, 'w') as file:
                        final_meta = {
                            "config": merged_config
                        }
                        file.write(json.dumps(final_meta))
        else:
            download_file(_file['url'], full_path)


def download_and_unzip(base_folder, item, wanted_hash):
    zip_path = os.path.join(base_folder, item['file'])
    hash_path = zip_path.replace('.zip', '.md5')
    download_file(item['url'], zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(base_folder)
    with open(hash_path, 'w') as file:
        file.write(wanted_hash)


def compare_and_download_zip(base_folder, item):
    md5_file = os.path.join(base_folder, item['file'].replace('.zip', '.md5'))
    wanted_hash = item['hash']
    if os.path.exists(md5_file):
        with open(md5_file, 'r') as file:
            content = file.read().rstrip()
        if content != wanted_hash:
            download_and_unzip(base_folder, item, wanted_hash)
    else:
        download_and_unzip(base_folder, item, wanted_hash)


def check_updates(_identity):
    if _identity == 'lib':
        return
    latest_info = get_latest_info()
    main_entry = latest_info['mainEntry']
    current_folder = get_absolute_path(".")
    compare_and_download_files(current_folder, main_entry['files'])
    for _platform in latest_info['platforms']:
        if _identity == _platform['identify']:
            compare_and_download_zip(current_folder, _platform)
    res_folder = get_absolute_path("resource")
    os.makedirs(res_folder, exist_ok=True)
    compare_and_download_files(res_folder, latest_info['resources'])
    compare_and_download_zip(current_folder, latest_info['vendors'])


def load_entry_from_module(_identify):
    if _identify == 'lib':
        from .lib import root
    elif _identify == '38-Darwin-x86_64':
        from .DarwinX6438 import root
    elif _identify == '39-Darwin-x86_64':
        from .DarwinX6439 import root
    elif _identify == '39-Darwin-arm64':
        from .DarwinArm6439 import root
    elif _identify == '38-Windows-AMD64':
        from .WindowsAMD6438 import root
    elif _identify == '39-Windows-AMD64':
        from .WindowsAMD6439 import root
    elif _identify == '38-Windows-x86':
        from .WindowsX8638 import root
    elif _identify == '38-Linux-x86_64':
        from .LinuxX6438 import root
    elif _identify == '39-Linux-x86_64':
        from .LinuxX6439 import root
    elif _identify == '311-Linux-x86_64':
        from .LinuxX64311 import root
    else:
        import aqt
        aqt.utils.showText('Unsupported platform:' + _identify)


identify = get_identify()


try:
    check_updates(identify)
except Exception as err:
    import aqt
    aqt.utils.showText('Unable to check updates, please check your network and retry\n' + str(err))
    pass

try:
    import packaging
except:
    _vendor_path = get_absolute_path("_vendor/_packaging")
    sys.path.insert(0, _vendor_path)

try:
    import openpyxl
except:
    _vendor_path = get_absolute_path("_vendor/_openpyxl")
    sys.path.insert(0, _vendor_path)

if __name__ != 'src':
    load_entry_from_module(identify)
