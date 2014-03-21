from ext.debugger.pox_proxy.database.cli import main
from subprocess import Popen
import sys
import code
import os
from threading import Timer


db = []
log = []
pox = []
mn = []
timer = None

debug_sample = [
        "ext.debugger.pox_proxy.of_01_debug",
        "--fake_debugger=0.1",
        "--flow_table_controller=flow_table_config.cfg",
        "forwarding.l2_learning",
        "forwarding.l3_learning"
        ]


def timer_callback():
    check_status()
    global timer
    timer = Timer(2.0, timer_callback)
    timer.start()


def check_status():
    global db, log, pox, mn

    terminated = []
    for p in db + log + pox + mn:
        if p.poll() != None:
            p.wait()
            print p.pid, "executed with code", p.returncode
            terminated.append(p)

    db = [p for p in db if p not in terminated]
    log = [p for p in log if p not in terminated]
    pox = [p for p in pox if p not in terminated]
    mn = [p for p in mn if p not in terminated]


def status():
    check_status()
    global db, log, pox, mn
    s = "Database:\n"
    s += "".join(["\t" + str(p.pid) + "\n" for p in db])
    s += "Log:\n"
    s += "".join(["\t" + str(p.pid) + "\n" for p in log])
    s += "POX:\n"
    s += "".join(["\t" + str(p.pid) + "\n" for p in pox])
    s += "Mininet:\n"
    s += "".join(["\t" + str(p.pid) + "\n" for p in mn])
    print s

def kill_all():
    kill_mn()
    kill_pox()
    kill_log()
    kill_db()

def stop_all():
    stop_mn()
    stop_pox()
    stop_log()
    stop_db()


def start(p):
    print "successfully started with pid:", p.pid
    return p

def db_console():
    main()
    sys.ps1 = "POX_ELT>"
    sys.ps2 = "..."

def start_db():
    global db
    p = Popen(("python", "-m", "ext.debugger.utility.start_db_server"),
              stdout=open("/dev/null", "w"))
    start(p)
    db.append(p)

def stop_db():
    global db
    p = Popen(("python", "-m", "ext.debugger.utility.stop_db_server"))
    db.append(p)

def kill_db():
    global db
    for p in db:
        p.kill()
    for p in db:
        p.wait()
    db = []


def start_log():
    global log
    p = Popen(("python", "-m", "ext.debugger.utility.start_log_server"),
              stdout=open("/dev/null", "w"))
    start(p)
    log.append(p)

def stop_log():
    global log
    p = Popen(("python", "-m", "ext.debugger.utility.stop_log_server"))
    log.append(p)

def kill_log():
    check_status()
    global log
    for p in log:
        p.kill()
    for p in log:
        p.wait()
    log = []


def start_pox(args=""):
    global pox
    if isinstance(args, tuple):
        p = Popen(("./pox.py", ) + args)
    elif isinstance(args, basestring):
        args = [a for a in args.split(" ") if a != ""]
        args = ["./pox.py"] + args
        p = Popen(args)
    elif isinstance(args, list):
        args = ["./pox.py"] + args
        p = Popen(args)
    else:
        raise Exception("Invalid args format")
    start(p)
    pox.append(p)

def kill_pox():
    global pox
    for p in pox:
        p.terminate()
    for p in pox:
        p.wait()
    pox = []

def stop_pox():
    kill_pox()


def start_mn(args=""):
    global mn
    if isinstance(args, tuple):
        p = Popen(("mn", ) + args)
    elif isinstance(args, basestring):
        args = [a for a in args.split(" ") if a != ""]
        args = ["mn"] + args
        p = Popen(args)
    elif isinstance(args, list):
        args = ["mn"] + args
        p = Popen(args)
    else:
        raise Exception("Invalid args format")
    start(p)
    mn.append(p)

def stop_mn():
    kill_mn()

def kill_mn():
    global mn
    for p in mn:
        p.terminate()
    for p in mn:
        p.wait()
    mn = []


def create_locals():
    l = globals()
    return l

def create_message():
    s = "Welcome to Error Localization Tool\n"
    s += "Usage:\n"
    s += "\tstatus()\n\n"
    s += "\tstop_all()\n"
    s += "\tkill_all()\n\n"
    s += "\tdb_console()\n\n"
    s += "\tstart_db()\n"
    s += "\tstop_db()\n"
    s += "\tkill_db()\n\n"
    s += "\tstart_log()\n"
    s += "\tstop_log()\n"
    s += "\tkill_log()\n\n"
    s += "\tstart_pox(args)\n"
    s += "\tstop_pox()\n"
    s += "\tkill_pox()\n\n"
    s += "\tstart_mn(args)\n"
    s += "\tstop_mn()\n"
    s += "\tkill_mn()\n\n"
    return s

def cli_main():
    timer_callback()
    sys.ps1 = 'POX_ELT>'
    sys.ps2 = '...'
    hello = create_message()
    l = create_locals()
    code.interact(hello, local=l)
    global timer
    timer.cancel()
    stop_all()
    kill_all()


if __name__ == '__main__':
    cli_main()
