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
deb='ext.debugger.pox_proxy.of_01_debug'
#echo $$ > stress_test.pid
touch stress_test.log
for size in 8;
do
    echo "*******" >> stress_test.log
    echo $size >> stress_test.log
    echo "*******" >> stress_test.log
    for len in 3;
    do
        echo ------- >> stress_test.log
        echo $len >> stress_test.log
        echo ------- >> stress_test.log
        for i in 0.1;
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
                run_term $terminal "./pox.py $deb --mult=$i forwarding.l2_learning forwarding.l3_learning"
                echo 'debug'
            fi
            pox_pid=$!
            run_term $terminal "python -m multiping --topo=line,$len,$size" "multiping.log"
            mn_pid=$!
            while ps -p $mn_pid > /dev/null; do sleep 0.5; done;
            kill -TERM $pox_pid
            python -m ext.debugger.utility.stop_log_server
            while ps -p $log_pid > /dev/null; do sleep 0.5; done;
            python -m ext.debugger.utility.stop_db_server
            while ps -p $db_pid > /dev/null; do sleep 0.5; done;
            echo $i >> stress_test.log
            tail -n 1 multiping.log >> stress_test.log;
        done;
    done;
done
