"""
Class for handling manifest files.
"""

# Copyright (c) 2014 Clarinova. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE.txt

import os.path
import re

class Manifest(object):

    def __init__(self, file_or_data):

        if os.path.exists(file_or_data):
            with open(file_or_data, 'r') as f:
                self.data = f.readlines()
                self.file = file_or_data
        else:

            if isinstance(file_or_data, list):
                self.data = file_or_data
            else:
                self.data = file_or_data.splitlines()
            self.file = None


    @property
    def documentation(self):

        in_doc_section = True # Start in doc mode

        doc_lines = []

        for line in self.data:

            if line.strip() == 'doc:':
                in_doc_section = True
                continue

            if re.match(r'^\w+:', line.strip()):
                in_doc_section = False
                continue

            if in_doc_section and line.strip():
                doc_lines.append(line)

        return '\n'.join(doc_lines)

    @property
    def sql(self):
        ''' Collect all of the SQL entries by driver. Each block can apply to
        multiple drivers.
        '''
        from collections import defaultdict

        in_sql_section = False
        drivers = None

        sql_lines = defaultdict(list)

        for line in self.data:

            m = re.match(r'^(\w+):\s*([\w+|\s]+)\s*', line)

            if m and m.group(1) == 'sql':
                in_sql_section = True
                drivers = [ d.strip() for d in m.groups()[1].split('|') ]

                continue

            if re.match(r'^\w+:', line.strip()):
                in_sql_section = False
                continue

            if in_sql_section and line.strip():
                for driver in drivers:
                    sql_lines[driver].append(line)



        return { driver:'\n'.join(lines) for driver, lines in sql_lines.items() }


    @property
    def partitions(self):

        in_partitions_section = False

        for line in self.data:
            line = line.strip()

            m = re.match(r'^(.*)#.*$', line)
            if m:
                line = m.groups()[0]

            if line == 'partitions:':
                in_partitions_section = True
                continue

            if re.match(r'^\w+:', line):
                in_partitions_section = False
                continue

            if in_partitions_section:
                if line.strip():
                    yield line.strip()


    @property
    def views(self):
        from collections import defaultdict

        def yield_lines(data):
            """Read all of the lines of the manifest and return the lines for views"""
            in_views_section = False
            in_view = False
            view_name = None


            for line in data:
                line = line.strip()

                if line.startswith('view:'): # Start of the views section

                    m = re.match(r'^view:\w*([^\#]+)', line)

                    if m and m.group(1):
                        view_name =  m.group(1).strip()
                        if view_name:
                            in_views_section = True
                            yield 'end', None, None
                            continue

                if re.match(r'^\w+:', line): # Start of some other section
                    in_views_section = False
                    yield 'end', None, None
                    continue

                if not in_views_section:
                    continue

                if re.match(r'create view', line.lower()):
                    yield 'end', None, None

                if line.strip():
                    yield 'viewline', view_name, line.strip()

            yield 'end', None, None

        view_lines = defaultdict(list)

        for cmd, view_name, line in yield_lines(self.data):
            if cmd == 'viewline':
                view_lines[view_name].append(line)

        for view_name, view_line in view_lines.items():
            yield view_name, ' '.join(view_line)

