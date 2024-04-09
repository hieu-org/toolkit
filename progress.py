import sys
import threading

from tqdm import tqdm

from .snippet import format_size_in_ib


class ProgressBar(tqdm):

    def update_to(self, n: int) -> None:
        self.update(n - self.n)


class ProgressPercentage(object):

    def __init__(self, filename, size=0):
        self._filename = filename
        self._size = size if size != 0 else 1
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" %
                (self._filename, format_size_in_ib(self._seen_so_far),
                 format_size_in_ib(self._size), percentage))
            sys.stdout.flush()
