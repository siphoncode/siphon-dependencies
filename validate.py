#!/usr/bin/env python3

import json
import os

def main():
    print('Checking syntax of version files...')
    dir_contents = os.listdir('versions')
    version_files = [f for f in dir_contents if '.json' in f]
    for vf in version_files:
        try:
            with open(os.path.join('versions', vf), 'r') as f:
                obj = json.loads(f.read())
            print('%s OK' % vf)
        except ValueError as e:
            print('%s invalid:' % vf)
            print(e)


if __name__ == '__main__':
    main()
