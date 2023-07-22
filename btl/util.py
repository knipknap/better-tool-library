import os
import hashlib

def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()

def file_is_newer(reference, file):
    return os.path.getmtime(reference) < os.path.getmtime(file)
