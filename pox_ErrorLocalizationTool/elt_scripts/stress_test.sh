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

terminal='no'
deb='ext.debugger.elt.of_01_debug'
log='stress_test.log'
mn_log='multiping.log'

touch $log
for size in 16;
do
    echo "*******" >> $log
    echo $size >> $log
    echo "*******" >> $log
    for len in 3;
    do
        echo ------- >> $log
        echo $len >> $log
        echo ------- >> $log
        for i in 0.01;
        do
            run_term $terminal 'python -m ext.debugger.utility.start_db_server'
            db_pid=$!
            run_term $terminal 'python -m ext.debugger.utility.start_log_server'
            log_pid=$!
            if [[ $i == "no" ]] ;
            then
                run_term $terminal "./pox.py forwarding.l2_learning"
                echo 'No debug'
            else
                run_term $terminal "./pox.py $deb --flow_table_controller=config/flow_table_config.cfg --fake_debugger=$i forwarding.l2_learning ext.debugger.controllers.interrupter"
                echo 'debug'
            fi
            pox_pid=$!
            run_term $terminal "python elt_scripts/multiping.py --topo=line,$len,$size" "$mn_log"
            mn_pid=$!
            while ps -p $mn_pid > /dev/null; do sleep 0.5; done;
            kill -TERM $pox_pid
            python -m ext.debugger.utility.stop_log_server
            while ps -p $log_pid > /dev/null; do sleep 0.5; done;
            python -m ext.debugger.utility.stop_db_server
            while ps -p $db_pid > /dev/null; do sleep 0.5; done;
            echo $i >> $log
            tail -n 1 $mn_log >> $log;
        done;
    done;
done
