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
run_term $terminal "adapters/pox/pox.py $deb --flow_table_controller=adapters/pox/config/flow_table_config.cfg openflow.discovery forwarding.l2_learning vermont_feeder debugger.verifier_adapter log.level --WARNING"
#" --flow_table_controller=config/flow_table_config.cfg forwarding.l2_learning ext.debugger.controllers.interrupter"
pox_pid=$!
#run_term $terminal "mn --topo=elt_test --custom `pwd`/adapters/pox/ext/debugger/topology/elt_test_topo.py --controller=remote"
run_term $terminal "sudo python netver/floodlight/disjoint_topo.py --remote=127.0.0.1:5555"
mn_pid=$!
run_term $terminal "./netver/veriserv -s netver/data/middle_boxes_disjoint.spec"
ver_pid=$!
run_term $terminal "./netver/proxyserv"
proxy_pid=$!
while ps -p $mn_pid > /dev/null; do sleep 0.5; done;
kill -TERM $pox_pid
python -m server.utility.stop_log_server
while ps -p $log_pid > /dev/null; do sleep 0.5; done;
python -m server.utility.stop_db_server
while ps -p $db_pid > /dev/null; do sleep 0.5; done;
kill -TERM $proxy_pid $ver_pid
