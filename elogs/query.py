class Eq(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def true(self, x):
        return x.attributes[self.key] == self.value


class Not(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def true(self, x):
        return x.attributes[self.key] != self.value


class Or(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def true(self, x):
        return x if self.left.true(x) or self.right.true(x) else None


class And(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def true(self, x):
        return x if self.left.true(x) and self.right.true(x) else None


class After(object):
    def __init__(self, when):
        self.when = when

    def true(self, x):
        return x if x.date >= self.when else None


class Before(object):
    def __init__(self, when):
        self.when = when

    def true(self, x):
        return x if x.date <= self.when else None


def query(logbook, condition):
    return [x for x in logbook.entries if condition.true(x)]
