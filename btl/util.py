import os
import hashlib
import xml.etree.ElementTree as ET

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

ns = {'s': 'http://www.w3.org/2000/svg'}

def get_abbreviations_from_svg(svg):
    try:
        tree = ET.fromstring(svg)
    except ET.ParseError:
        return {}

    result = {}
    for text_elem in tree.findall('.//s:text', ns):
        id = text_elem.attrib.get('id', ns)
        if id is None:
            continue

        abbr = text_elem.text
        if abbr is not None:
            result[id.lower()] = abbr

        span_elem = text_elem.find('.//s:tspan', ns)
        if span_elem is None:
            continue
        abbr = span_elem.text
        result[id.lower()] = abbr

    return result

if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    with open(filename) as fp:
        svg = fp.read()
    print(get_abbreviations_from_svg(svg))
