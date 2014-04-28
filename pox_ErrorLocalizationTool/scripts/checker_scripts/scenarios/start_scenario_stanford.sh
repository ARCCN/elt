cd ..
gnome-terminal --tab -e './pox.py openflow.of_01 --port=6632 openflow.discovery debugger.controllers.stanford_controller' \
 --tab -e 'sudo mn --topo=stanford --custom /home/lantame/SDN/mininet/custom/stanford.py --switch=ovsk --controller=remote,port=6633 --mac' \
 --tab -e './proxy_start.py'
