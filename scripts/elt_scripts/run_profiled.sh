#!/bin/bash

rm -f profile/*.prof

#sed -i -e "s/profiled = \"\"/profiled = \"handle_PACKET_IN\"/"  adapters/pox/ext/debugger/elt/of_01_debug/of_01_debug.py
#./scripts/elt_scripts/stress_test.sh $1
#sed -i -e "s/profiled = \"handle_PACKET_IN\"/profiled = \"save_info\"/" adapters/pox/ext/debugger/elt/of_01_debug/of_01_debug.py
#./scripts/elt_scripts/stress_test.sh $1
#sed -i -e "s/profiled = \"save_info\"/profiled = \"\"/" adapters/pox/ext/debugger/elt/of_01_debug/of_01_debug.py

if [[ $1 == "dist" || $1 == "" ]];
then
    #sed -i -e "s/#@profile/@profile/" adapters/pox/ext/debugger/elt/debuggers/dist_flow_table_controller.py
    #./scripts/elt_scripts/stress_test.sh $1
    #sed -i -e "s/@profile/#@profile/" adapters/pox/ext/debugger/elt/debuggers/dist_flow_table_controller.py

    sed -i -e "s/#@profile/@profile/" adapters/pox/ext/debugger/elt/debuggers/dist_flow_table.py
    ./scripts/elt_scripts/stress_test.sh $1
    sed -i -e "s/@profile/#@profile/" adapters/pox/ext/debugger/elt/debuggers/dist_flow_table.py
else
    #sed -i -e "s/#@profile/@profile/" adapters/pox/ext/debugger/elt/debuggers/flow_table_controller.py
    #./scripts/elt_scripts/stress_test.sh $1
    #sed -i -e "s/@profile/#@profile/" adapters/pox/ext/debugger/elt/debuggers/flow_table_controller.py

    sed -i -e "s/#@profile/@profile/" adapters/pox/ext/debugger/elt/debuggers/flow_table.py
    ./scripts/elt_scripts/stress_test.sh $1
    sed -i -e "s/@profile/#@profile/" adapters/pox/ext/debugger/elt/debuggers/flow_table.py
fi

#sed -i -e "s/#@profile/@profile/" server/ext/debugger/elt/database/database.py
#./scripts/elt_scripts/stress_test.sh $1
#sed -i -e "s/@profile/#@profile/" server/ext/debugger/elt/database/database.py
