import ctypes
import json
import logging
import os
import platform
import signal
import uuid
import zipfile
from datetime import datetime, timezone
from functools import reduce
from http import HTTPStatus

import numpy as np
import psutil

from .constant import FILE_ATTRIBUTE_HIDDEN, FTIME_YYYYMMDD


def build_response_status(code: int, message: str = "", params={}):
    return {"code": code, "message": message, "params": params}


# Return current time in UTC with precision in seconds.
def get_unix_utc_timestamp():
    return int(datetime.now(tz=timezone.utc).timestamp())


def get_utc_yyyymmdd():
    return f'{datetime.now(tz=timezone.utc).strftime(FTIME_YYYYMMDD)}'


def hhmmss_to_secs(hhmmss):
    """
    Convert hhmmss to seconds
    :param hhmmss:
    :return: totals seconds
    """
    h, m, s = 0, 0, 0
    if len(hhmmss) == 6:
        h = int(hhmmss[:2])  # Extract the first two characters as hours
        m = int(
            hhmmss[2:4])  # Extract the characters from index 2 to 4 as minutes
        s = int(hhmmss[4:])  # Extract the remaining characters as seconds
    total_seconds = (h * 3600) + (m * 60) + s
    return total_seconds


def path_has_wildcard(path: str) -> bool:
    """
    Whether path already has image wildcard
    """
    for ext_pat in ['*.raw', '*.bmp', '*.png', '*.jpg']:
        if path.endswith(ext_pat):
            return True
    return False


def get_env():
    env = 'development'
    if 'SERVER_ENV' in os.environ:
        env = os.environ['SERVER_ENV']
    env = f'\nSERVER_ENV = {env}'
    return env


def get_mac_address():
    mac_address = uuid.getnode()
    mac_address_hex = ':'.join([
        '{:02x}'.format((mac_address >> elements) & 0xff)
        for elements in range(0, 8 * 6, 8)
    ][::-1])
    return mac_address_hex


def create_hidden_dir(dir_name):
    os_name = platform.system()

    if os_name == "Windows":
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

            ret = ctypes.windll.kernel32.SetFileAttributesW(
                dir_name, FILE_ATTRIBUTE_HIDDEN)

            if ret:
                logging.info(f'Directory {dir_name} was made hidden.')
            else:  # If the operation failed, GetLastError will give more info.
                error = ctypes.windll.kernel32.GetLastError()
                logging.error(f'Failed to hide directory. Error code: {error}')
    else:  # assuming Unix-based system
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            logging.info(f'Directory {dir_name} was made hidden.')


def is_hidden_dir(dir_name):
    os_name = platform.system()

    result = False
    if os_name == "Windows":
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(dir_name)
            assert attrs != -1
            result = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
        except (AttributeError, AssertionError):
            result = False
    else:  # assuming Unix-based system
        name = os.path.basename(dir_name)
        result = name.startswith('.')
    return result


def format_size_in_ib(size_in_ib):
    """
    Convert the size of a file from ibibytes to either kibibytes, mebibytes, or gibibytes, depending on the size.
    :param size_in_ib: The file size in ibibytes.
    :return: A string that represents the file size in either ibibytes, kibibytes, mebibytes or gibibytes.
    """
    # Convert size to KiB and MiB
    size_in_kib = size_in_ib / 1024
    size_in_mib = size_in_kib / 1024
    size_in_gib = size_in_mib / 1024

    # Use the largest unit in which the size is greater than or equal to 1
    if size_in_gib >= 1:
        return f'{size_in_gib:.2f} GiB'
    if size_in_mib >= 1:
        return f'{size_in_mib:.2f} MiB'
    elif size_in_kib >= 1:
        return f'{size_in_kib:.2f} KiB'
    else:
        return f'{size_in_ib} ib'


def format_ratio_as_percent(length, total):
    percent = 0
    if total != 0:
        percent = length / total * 100
    return f'{percent:.0f}%'


def string_to_enum(enum_class, string_value):
    try:
        return enum_class[string_value.upper()]
    except KeyError:
        raise ValueError(
            f"'{string_value}' is not a valid value for {enum_class.__name__}")


def get_nested_value_from_config(key_path: str, json_config=None):
    try:
        value = reduce(lambda d, k: d[k], key_path.split('/'), json_config)
    except (KeyError, TypeError):
        value = None
    return value


def get_disk_usage_percent():
    try:
        # Get the current working directory
        current_directory = os.getcwd()
        # Get the device of the file system containing the specified path
        st_dev = os.stat(current_directory).st_dev
        # Find the corresponding partition for the device
        partition = next(p for p in psutil.disk_partitions(all=False)
                         if os.stat(p.mountpoint).st_dev == st_dev)

        disk_usage = psutil.disk_usage(partition.mountpoint)
        if disk_usage.percent > 85:
            return f"Low Disk Space: {disk_usage.percent: .2f} used%", HTTPStatus.BAD_REQUEST
        return f"Disk Space used: {disk_usage.percent: .2f}%", HTTPStatus.OK
    except Exception as e:
        return f"Error: {e}", HTTPStatus.BAD_REQUEST


def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        logging.error(f"Error: {e}")


def save_json_file(json_file_path: str, json_content: dict):
    """
    save json to file
    :param json_file_path:
    :param json_content:
    :return:
    """
    with open(json_file_path, 'w') as json_file:
        json.dump(json_content, json_file, indent=4)


def load_json_file(json_file_path: str):
    """
    load json file
    :param json_file_path:
    :return:
    """
    # Check if the file exists
    if not os.path.exists(json_file_path):
        logging.info(f'No such file: {json_file_path}')
        return {}  # Returning an empty dictionary

    with open(json_file_path, 'r') as backup_file:
        json_content = json.load(backup_file)

    return json_content


def file_split(file_path, max_file_size):
    """
    Split file into pieces, each piece's size is at most MAX_FILE_SIZE bytes.
    """
    part_files = []
    part_num = 1
    with open(file_path, 'rb') as src:
        while True:
            chunk = src.read(max_file_size)
            if not chunk:
                break
            part_file = f'{file_path}.{part_num:03d}'
            with open(part_file, 'wb') as tgt:
                tgt.write(chunk)
            part_files.append(part_file)
            part_num += 1
    return part_files


def zip_file(file_path: str):
    """
    Compresses the given file into a zip archive.
    """
    file_name = os.path.basename(file_path)
    zip_file_path = os.path.join(os.path.dirname(file_path),
                                 f'{file_name}.zip')
    logging.info(f'Zipping file: {file_path}')

    with zipfile.ZipFile(zip_file_path, 'w',
                         compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(file_path, arcname=file_name)

    return zip_file_path


def kill_process(pid):
    """
    Kill process with process ID.
    :param pid: Process ID (integer).
    :return: True if the process was successfully killed, False otherwise.
    """
    try:
        process_name = psutil.Process(pid).name()
        os.kill(pid, signal.SIGTERM)  # Send termination signal
        logging.info(f'Killed process {process_name}')
        return True
    except OSError:
        return False  # Failed to kill the process


def getenv_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in "true"
