# -*- coding: utf-8 -*-
import hashlib
import json
import os
import platform
import sys
import urllib
import zipfile
from pathlib import Path

from aqt import utils


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
        utils.showWarning('Ultimate Addon has been updated, please restart Anki')


def get_latest_info():
    remote_url = 'https://ankiultimate.github.io/main.json'
    req = urllib.request.Request(remote_url)
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


def download_and_unzip(base_folder, url, wanted_hash):
    zip_path = os.path.join(base_folder, "vendors.zip")
    hash_path = os.path.join(base_folder, "vendors.md5")
    download_file(url, zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(base_folder)
    with open(hash_path, 'w') as file:
        file.write(wanted_hash)

def compare_and_download_vendors(base_folder, vendor):
    md5_file = os.path.join(base_folder, "vendors.md5")
    wanted_hash = vendor['hash']
    if os.path.exists(md5_file):
        with open(md5_file, 'rb') as file:
            content = file.read()
        if content != wanted_hash:
            download_and_unzip(base_folder, vendor['url'], wanted_hash)
    else:
        download_and_unzip(base_folder, vendor['url'], wanted_hash)


def check_updates(_identify):
    latest_info = get_latest_info()
    if _identify != 'lib':
        main_entry = latest_info['mainEntry']
        compare_and_download_files(get_absolute_path(main_entry['baseFolder']), main_entry['files'])
    for _platform in latest_info['platforms']:
        if _identify == _platform['identify']:
            base_folder = get_absolute_path(_platform['baseFolder'])
            os.makedirs(base_folder, exist_ok=True)
            compare_and_download_files(base_folder, _platform['files'])
    res_folder = get_absolute_path("resource")
    os.makedirs(res_folder, exist_ok=True)
    compare_and_download_files(res_folder, latest_info['resources'])
    compare_and_download_vendors(res_folder, latest_info['vendors'])

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
        utils.showText('Unsupported platform:' + _identify)


identify = get_identify()


try:
    check_updates(identify)
except Exception as err:
    utils.showText('Unable to check updates, please check your network and retry\n' + str(err))
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

try:
    import qtpy
except:
    _vendor_path = get_absolute_path("_vendor/_qtpy")
    sys.path.insert(0, _vendor_path)

load_entry_from_module(identify)
