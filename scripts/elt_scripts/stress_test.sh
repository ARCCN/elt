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

terminal='no'
deb='ext.debugger.elt.of_01_debug'
log='stress_test.log'
mn_log='multiping.log'
CONTROLLERS=2
ports=""

function get_ports {
    case $CONTROLLERS in
        "0" )   ports="" ;;
        "1" )   ports="6633" ;;
        *   )   for (( i=0; i<$CONTROLLERS; ++i )); do ports=$ports" "$((6640+$i)); done ;;
    esac
}

mkfifo stress_test.fifo
rm -f pid

for iter in "";
do
    log="stress_test$iter.log"
    touch $log
    for size in 8 16 32 64;
    do
        echo "*******" >> $log
        echo $size >> $log
        echo "*******" >> $log
        for len in 1 2 3 4 5;
        do
            echo ------- >> $log
            echo $len >> $log
            echo ------- >> $log
            for i in no 0.0 0.01 0.1 0.5;
            do
                run_term $terminal 'python -m server.utility.start_db_server'
                db_pid=$!
                run_term $terminal 'python -m server.utility.start_log_server'
                log_pid=$!
                get_ports
                echo PORTS: $ports
                retransmit=""
                cid=0
                for port in $ports ; do
                    if [[ $i == "no" ]] ;
                    then
                        run_term $terminal "./wrap.sh tail -f stress_test.fifo | adapters/pox/pox.py openflow.of_01 --address=127.0.0.1 --port=$port py log.level --WARNING forwarding.l2_learning $retransmit"
                        echo 'no proxy'
                    elif [[ $i == "proxy" ]];
                    then
                        run_term $terminal "./wrap.sh tail -f stress_test.fifo | adapters/pox/pox.py py log.level --WARNING $deb --cid=$cid --address=127.0.0.1 --port=$port forwarding.l2_learning $retransmit ext.debugger.controllers.interrupter --rate=0.0"
                        echo 'just proxy'
                    else
                        run_term $terminal "./wrap.sh tail -f stress_test.fifo | adapters/pox/pox.py py log.level --WARNING $deb --cid=$cid --address=127.0.0.1 --port=$port --dist_flow_table_controller=adapters/pox/config/flow_table_config.cfg forwarding.l2_learning $retransmit ext.debugger.controllers.interrupter --rate=$i flamer"
                        #" --flow_table_controller=config/flow_table_config.cfg forwarding.l2_learning ext.debugger.controllers.interrupter"
                        echo 'debug'
                    fi
                    retransmit="--retransmit=False"
                    cid=$(($cid+1))
                done;
                #pox_pid=`cat pid`
                #echo "Read $pox_pid"
                #rm pid
                echo $i >> $log
                sleep 15
                #read
                run_term $terminal "python scripts/elt_scripts/multiping.py --topo=line,$len,$size" "$log"
                mn_pid=$!
                while ps -p $mn_pid > /dev/null; do sleep 0.5; done;
                pox_pid=`cat pid`
                echo "Read $pox_pid"
                echo "Killing $pox_pid"

                rm pid
                kill -TERM $pox_pid
                python -m server.utility.stop_log_server
                while ps -p $log_pid > /dev/null; do sleep 0.5; done;
                python -m server.utility.stop_db_server
                while ps -p $db_pid > /dev/null; do sleep 0.5; done;
            done;
        done;
    done;
done

rm stress_test.fifo
