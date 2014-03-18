from ext.debugger.pox_proxy.database.cli import *

if __name__ == '__main__':
    cli = CLI()
    sys.ps1 = 'POX_ELT>'
    sys.ps2 = '...'
    hello, l = cli.run()
    code.interact(hello, local=l)
