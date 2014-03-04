terminal='xterm'
deb='ext.debugger.pox_proxy.of_01_debug'
$terminal -e 'python -m ext.debugger.utility.start_db_server' &
$terminal -e 'python -m ext.debugger.utility.start_log_server' &
$terminal -e 'sudo python -m multiping --topo=line,1,4' &
$terminal -e 'python ./pox.py $deb --mult=0.0 forwarding.l2_learning' ; python -m ext.debugger.utility.stop_log_server ; python -m ext.debugger.utility.stop_db_server
