#!/bin/bash
function run_term {
    if [[ $1 == "no" ]] ;
    then
        if [[ $3 != "" ]];
        then
            $2 > $3 &
        else
            $2 &
        fi
    else
        if [[ $3 != "" ]];
        then
            $1 -e "$2 > $3" &
        else
            $1 -e "$2" &
        fi
    fi
}

terminal='xterm'
deb='ext.debugger.elt.of_01_debug'
log='elt_test.log'
mn_log='multiping.log'

run_term $terminal 'python -m server.utility.start_db_server'
db_pid=$!
run_term $terminal 'python -m server.utility.start_log_server'
log_pid=$!
run_term $terminal "adapters/pox/pox.py $deb --dist_flow_table_controller=adapters/pox/config/flow_table_config.cfg ext.debugger.controllers.router ext.debugger.controllers.server ext.debugger.controllers.monitor py log.level --WARNING"
#" --flow_table_controller=config/flow_table_config.cfg forwarding.l2_learning ext.debugger.controllers.interrupter"
pox_pid=$!
run_term $terminal "mn --topo=elt_test --custom `pwd`/adapters/pox/ext/debugger/topology/elt_test_topo.py --controller=remote"
mn_pid=$!
while ps -p $mn_pid > /dev/null; do sleep 0.5; done;
kill -TERM $pox_pid
python -m server.utility.stop_log_server
while ps -p $log_pid > /dev/null; do sleep 0.5; done;
python -m server.utility.stop_db_server
while ps -p $db_pid > /dev/null; do sleep 0.5; done;
