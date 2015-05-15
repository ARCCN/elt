#!/bin/bash
function run_term {
    if [[ $1 == "no" ]] ;
    then
        if [[ $3 != "" ]];
        then
            bash -c "$2" >> $3 &
        else
            bash -c "$2" &
        fi
    else
        if [[ $3 != "" ]];
        then
            $1 -e "$2 >> $3" &
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
run_term $terminal "adapters/pox/pox.py $deb --port=6640 --cid=1 --dist_flow_table_controller=adapters/pox/config/flow_table_config.cfg ext.debugger.controllers.router ext.debugger.controllers.monitor py log.level --WARNING"
pox_pid="$pox_pid $!"
run_term $terminal "adapters/pox/pox.py $deb --port=6641 --cid=2 --dist_flow_table_controller=adapters/pox/config/flow_table_config.cfg ext.debugger.controllers.server ext.debugger.controllers.monitor py log.level --WARNING"
#" --flow_table_controller=config/flow_table_config.cfg forwarding.l2_learning ext.debugger.controllers.interrupter"
pox_pid="$pox_pid $!"
sleep 5
run_term $terminal "sudo python scripts/elt_scripts/mn_elt_test.py"
# run_term $terminal "mn --topo=elt_test --custom `pwd`/adapters/pox/ext/debugger/topology/elt_test_topo.py --controller=remote,127.0.0.1,6640;remote,127.0.0.1,6641"
mn_pid=$!
while ps -p $mn_pid > /dev/null; do sleep 0.5; done;
kill -TERM $pox_pid
python -m server.utility.stop_log_server
while ps -p $log_pid > /dev/null; do sleep 0.5; done;
python -m server.utility.stop_db_server
while ps -p $db_pid > /dev/null; do sleep 0.5; done;
