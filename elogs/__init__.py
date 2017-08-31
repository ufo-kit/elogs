import os
import dateutil.parser


class Entry(object):

    SEPARATOR = '========================================'

    def __init__(self, lines):
        self.attributes = {}

        index = lines.index(self.SEPARATOR)

        for line in lines[:index]:
            key, value = line.split(':', 1)
            self.attributes[key.decode('iso-8859-1')] = value.lstrip().decode('iso-8859-1')

        self.comment = ''.join(lines[index+1:]).decode('iso-8859-1')
        self.id = int(self.attributes.get('$@MID@$', -1))
        self.date = dateutil.parser.parse(self.attributes['Date'])

    def __repr__(self):
        return '<Entry:id={}>'.format(self.id)


def parse_entries(path):
    def group_entries(lines):
        group = []

        for line in lines:
            if line.startswith('$@MID@$'):
                if group:
                    yield group
                    group = []

            group.append(line.rstrip())

        yield group

    with open(path) as f:
        return (Entry(g) for g in group_entries(f.readlines()))


def absolute_entries(path):
    return (os.path.join(path, x) for x in sorted(os.listdir(path)))


def dir_entries(entries):
    return (x for x in entries if os.path.isdir(x))


class Logbook(object):
    def __init__(self, path):
        self.entries = {}

        for subdir in dir_entries(absolute_entries(path)):
            entries = (os.path.join(subdir, x) 
                    for x in sorted(os.listdir(subdir)) 
                    if x.endswith('.log'))

            for log in entries:
                self.entries.update({x.id: x for x in parse_entries(log)})


class Storage(object):
    def __init__(self, path):
        self.logbooks = {}

        for subdir in dir_entries(absolute_entries(path)):
            self.logbooks[os.path.basename(subdir)] = Logbook(subdir)
