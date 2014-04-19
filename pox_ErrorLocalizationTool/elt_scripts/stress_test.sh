#!/bin/bash
function run_term {
    if [[ $1 == "no" ]] ;
    then
        if [[ $3 != "" ]];
        then
            $2 >> $3 &
        else
            $2 &
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

terminal='no'
deb='ext.debugger.elt.of_01_debug'
log='stress_test.log'
mn_log='multiping.log'

for iter in "";
do
    log="stress_test$iter.log"
    touch $log
    for size in 64;
    do
        echo "*******" >> $log
        echo $size >> $log
        echo "*******" >> $log
        for len in 5;
        do
            echo ------- >> $log
            echo $len >> $log
            echo ------- >> $log
            for i in no proxy 0.0 0.01 0.1 0.5;
            do
                run_term $terminal 'python -m ext.debugger.utility.start_db_server'
                db_pid=$!
                run_term $terminal 'python -m ext.debugger.utility.start_log_server'
                log_pid=$!
                if [[ $i == "no" ]] ;
                then
                    run_term $terminal "./pox.py log.level --WARNING forwarding.l2_learning"
                    echo 'no proxy'
                elif [[ $i == "proxy" ]];
                then
                    run_term $terminal "./pox.py log.level --WARNING $deb forwarding.l2_learning ext.debugger.controllers.interrupter --rate=0.0"
                    echo 'just proxy'
                else
                    run_term $terminal "./pox.py log.level --WARNING $deb --flow_table_controller=config/flow_table_config.cfg forwarding.l2_learning ext.debugger.controllers.interrupter --rate=$i"
                    #" --flow_table_controller=config/flow_table_config.cfg forwarding.l2_learning ext.debugger.controllers.interrupter"
                    echo 'debug'
                fi
                pox_pid=$!
                echo $i >> $log
                run_term $terminal "python elt_scripts/multiping.py --topo=line,$len,$size" "$log"
                mn_pid=$!
                while ps -p $mn_pid > /dev/null; do sleep 0.5; done;
                kill -TERM $pox_pid
                python -m ext.debugger.utility.stop_log_server
                while ps -p $log_pid > /dev/null; do sleep 0.5; done;
                python -m ext.debugger.utility.stop_db_server
                while ps -p $db_pid > /dev/null; do sleep 0.5; done;
            done;
        done;
    done;
done
