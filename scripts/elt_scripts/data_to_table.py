import sys

f = open(sys.argv[1], "r")
table = {}

# Data: #h #sw latency total
for line in f:
    if line.isspace():
        continue
    l = line.split(" ")
    table.setdefault((int(l[0]), int(l[1])), []).append(l[2])
f.close()

print "\n".join((" ".join((list(map(str, k)) + table[k])) for k in sorted(table)))
