import os
import threading
import Queue
import multiprocessing
import dateutil.parser

try:
    import inotify.adapters
    import inotify.constants
    HAVE_INOTIFY = True
except ImportError:
    HAVE_INOTIFY = False


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


def do_watch(path, reload_queue):
    notifier = inotify.adapters.Inotify()
    mask = inotify.constants.IN_CLOSE_WRITE | inotify.constants.IN_DELETE
    paths = []

    for logbook_path in dir_entries(absolute_entries(path)):
        for year_path in dir_entries(absolute_entries(logbook_path)):
            notifier.add_watch(year_path, mask=mask)
            paths.append(year_path)

    try:
        for event in notifier.event_gen():
            if event is not None:
                logbook_path = os.path.dirname(event[2])
                reload_queue.put(logbook_path)
    except KeyboardInterrupt:
        for path in paths:
            notifier.remove_watch(path)


class Storage(object):
    def __init__(self, path, watch=False):
        self.logbooks = {}

        for subdir in dir_entries(absolute_entries(path)):
            self.logbooks[os.path.basename(subdir)] = Logbook(subdir)

        if not watch:
            return

        if not HAVE_INOTIFY:
            raise RuntimeError("inotify is not installed")

        def update_logbooks(process, reload_queue):
            while process.is_alive():
                try:
                    path = reload_queue.get(True, 1)
                    name = os.path.basename(path)

                    # XXX: race conditiony ...
                    del self.logbooks[name]
                    self.logbooks[name] = Logbook(path)
                except Queue.Empty:
                    pass

        reload_queue = multiprocessing.Queue()

        # We are supposed to run inotify handling in a separate process to
        # avoid weird GIL locking problems. We use a queue to get the paths
        # that need be reload.
        process = multiprocessing.Process(target=do_watch, args=(path, reload_queue))
        process.start()

        # To avoid blocking on the queue, we set up a thread to communicate
        # with the inotify process.
        thread = threading.Thread(target=update_logbooks, args=(process, reload_queue))
        thread.start()
