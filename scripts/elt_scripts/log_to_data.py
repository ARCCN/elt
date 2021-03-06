import re
import sys


hosts = None
match = None


def get_data(filename, val='0.0'):
    global hosts, match
    hosts = re.compile('\*\n([0-9]*)\n\*')
    match = re.compile(
        '-\n([0-9]*).*?' +
        val + '\n' +
        '.*?, ([0-9\.]*) in ([0-9\.]*)',
        flags=re.DOTALL)
    data = []
    fin = open(filename, 'r')
    s = fin.read()
    h = [m for m in hosts.finditer(s)]
    for i in range(len(h)-1):
        for m in match.finditer(s, h[i].end(), h[i+1].start()):
            data.append((h[i].group(1), m.group(1), m.group(2), m.group(3)))
    if len(h) > 0:
        for m in match.finditer(s, h[-1].end()):
            data.append((h[-1].group(1), m.group(1), m.group(2), m.group(3)))
    data = [(int(a), int(b), float(c), float(d)) for a, b, c, d in data]
    return data

if __name__ == '__main__':
    val = sys.argv[2]
    val = val.replace('.', '\.')
    fn = sys.argv[1]
    data = get_data(fn, val)
    for a, b, c, d in data:
        print a, b, c, d
