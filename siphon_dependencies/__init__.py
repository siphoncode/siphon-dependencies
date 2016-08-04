#!/usr/bin/env python3

import json
import requests
import sys
from termcolor import colored

BITBUCKET_API_KEY = 't2k6px3bvoUGfvwxX14F87W81mHJuZT2'
DEPENDENCY_FILE = 'https://getsiphon:{api_key}@bitbucket.org/getsiphon/' \
                  'siphon-dependencies/raw/master/versions/{version}.json'

def yn(msg):
    try:
        valid_response = False
        while not valid_response:
            response = input(msg) or 'y'
            if response == 'y' or response == 'Y':
                return True
            elif response == 'n' or response == 'N':
                return False
            else:
                msg = 'Please enter \'y\' or \'n\': '
    except KeyboardInterrupt:
        return False

class DictDiff(object):
    def __init__(self, new_dict, old_dict):
        """
        Takes two dicts and provides methods for finding differences between
        them.

        Each method is self explanatory and returns a dictionary.
        """
        self.new_dict = new_dict
        self.old_dict = old_dict
        self.new_dict_keys = set(new_dict.keys())
        self.old_dict_keys = set(old_dict.keys())
        self.intersection = self.new_dict_keys.intersection(self.old_dict_keys)

    def added(self):
        keys = self.new_dict_keys - self.intersection
        return DictDiff._sub_dict(self.new_dict, keys)

    def print_added(self):
        added = self.added()
        for k in added:
            print(colored('+ %s %s' % (k, added[k]), 'green'))

        if not added:
            print('None')

    def removed(self):
        keys = self.old_dict_keys - self.intersection
        return DictDiff._sub_dict(self.old_dict, keys)

    def print_removed(self):
        removed = self.removed()
        for k in removed:
            print(colored('- %s %s' % (k, removed[k]), 'red'))

        if not removed:
            print('None')

    def modified(self):
        # Check the values of the keys that have not changes to see if they
        # have been modified.
        old_same = DictDiff._sub_dict(self.old_dict, self.intersection)
        new_same = DictDiff._sub_dict(self.new_dict, self.intersection)

        modified = {}
        for k in old_same:
            if old_same[k] != new_same[k]:
                modified[k] = new_same[k]

        return modified

    def print_modified(self):
        modified = self.modified()
        for k in modified:
            print(k)
            print(colored('+ %s' % self.new_dict[k], 'green'))
            print(colored('- %s' % self.old_dict[k], 'red'))

        if not modified:
            print('None')

    def same(self):
        keys = self.intersection - set(self.modified().keys())
        return DictDiff._sub_dict(self.new_dict, keys)

    def print_same(self):
        same = self.same()
        for k in same:
            print('%s %s' % (k, same[k]))

        if not same:
            print('None')

    @staticmethod
    def _sub_dict(d, keys):
        # Returns a sub-dictionary of a given dictionary as determined by a
        # list of keys.
        sub = {}
        for k in keys:
            sub[k] = d[k]
        return sub

class Dependencies(object):
    def __init__(self, version):
        self._data = self._load_data(version)
        self.version = version
        self.dependency_data = self._data['dependencies']

    @staticmethod
    def _load_data(version):
        url = DEPENDENCY_FILE.format(api_key=BITBUCKET_API_KEY,
              version=version)
        r = requests.get(url)
        data = r.json()
        return data

    def dependency_list(self, platform=None):
        '''
        Returns an alphabetized list of node dependencies. Pass in the platform
        to receive platform specific dependencies
        '''
        assert(platform in (None, 'ios', 'android'))

        deps = []
        if platform:
            for d in self.dependency_data:
                if platform in self.dependency_data[d]['platforms']:
                    deps.append(d)
        else:
            deps = list(self.dependency_data.keys())
        return sorted(deps)

    def update_package_file(self, pkg_path, env='production'):
        """
        Updates the dependencies in the given package.json file
        """
        print(colored('Updating package.json file...', 'yellow'))
        pkg_obj = {}
        with open(pkg_path, 'r') as f:
            pkg_obj = json.loads(f.read())

        new_deps = {}
        for d in self.dependency_data:
            new_deps[d] = self.dependency_data[d][env]

        dict_diff = DictDiff(new_deps, pkg_obj['dependencies'])
        print(colored('New modules:', 'yellow'))
        dict_diff.print_added()
        print(colored('Removed modules:', 'yellow'))
        dict_diff.print_removed()
        print(colored('Modified modules:', 'yellow'))
        dict_diff.print_modified()
        print(colored('Unchanged modules:', 'yellow'))
        dict_diff.print_same()

        proceed = yn(colored('\nYour local package.json file will be ' \
        'overwritten. Continue? [Y/n] ', 'yellow'))

        if not proceed:
            sys.exit(1)

        # Update the package.json object and write it
        pkg_obj['dependencies'] = new_deps
        pkg_string = json.dumps(pkg_obj, indent=2, sort_keys=True)

        # Write the updated package object to the package.json file
        with open(pkg_path, 'w') as f:
            f.write(pkg_string)
        print('Done')
