#!/usr/bin/python3
import os
import sys
import argparse
import json
from tooldb import ToolDB, serializers

parser = argparse.ArgumentParser(
    prog=__file__,
    description='CLI tool to manage a tool library'
)

# Common arguments
parser.add_argument('-f', '--format',
                    help='the type (format) of the library',
                    choices=sorted(serializers.serializers.keys()),
                    default='freecad')
parser.add_argument('name',
                    help='the DB name. In case of a file based DB, this is the path to the DB')
subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')

# "ls" command arguments
lsparser = subparsers.add_parser('ls', help='list objects')
lsparser.add_argument('objects',
                      help='which DB object to work with',
                      nargs='*',
                      choices=['all', 'libraries', 'tools'])

# "export" command arguments
exportparser = subparsers.add_parser('export', help='export objects in a defined format')
exportparser.add_argument('-f', '--format',
                          dest='output_format',
                          help='target format',
                          choices=sorted(serializers.serializers.keys()),
                          required=True)
exportparser.add_argument('output',
                          help='the output DB name. In case of a file based DB, this is the path to the DB')


args = parser.parse_args()

serializer_cls = serializers.serializers[args.format]
serializer = serializer_cls(args.name)
db = ToolDB()
db.deserialize(serializer)

if args.command == 'ls':
    for obj in args.objects:
        if obj == 'libraries':
            for lib in db.libraries:
                print(lib)
        elif obj == 'tools':
            for tool in db.tools:
                print(tool)
        elif obj == 'all' or not obj:
            db.dump(serializer)
        else:
            parser.error('invalid object requested: {}'.format(args.object))

elif args.command == 'export':
    output_serializer_cls = serializers.serializers[args.output_format]
    output_serializer = serializer_cls(args.output)
    db.serialize(output_serializer)

else:
    print("no command given, nothing to do")
