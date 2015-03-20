from glob import glob
import json


files=glob("*.dmp")
for f in files:
    out = open(f + ".1", "w")
    for s in open(f):
        d = json.loads(s)
        del d["time"]
        for g in d["entry_groups"]:
            for e in g["entries"]:
                try:
                    del e["data"]["flags"]
                except:
                    pass
                try:
                    del e["data"]["name"]
                except:
                    pass
                try:
                    del e["data"]["command"]
                except:
                    pass
                try:
                    del e["name"]
                except:
                    pass
        s = json.dumps(d)
        out.write(s + "\n")
    out.close()



