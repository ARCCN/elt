cd ..
gnome-terminal --tab -e './pox.py openflow.of_01 --port=6632 openflow.discovery debugger.controllers.single_entranced_controller_1' \
 --tab -e 'sudo mn --topo=single_entranced --custom /home/lantame/mininet/custom/single_entranced_1.py --switch=ovsk --controller=remote,port=6633 --mac --arp' \
 --tab -e './proxy_start.py'
