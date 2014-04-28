cd ..
gnome-terminal --tab -e './pox.py openflow.of_01 --port=6632 openflow.discovery debugger.controllers.single_entranced_controller_2' \
 --tab -e 'sudo mn --topo=single_entranced --custom /home/lantame/SDN/mininet/custom/single_entranced_2.py --switch=ovsk --controller=remote,port=6633 --mac' \
 --tab -e './proxy_start.py'
