# ryu-ares-codes

sudo mn --custom  ./provisioning-topology.py --topo provisioning --mac --controller
ryu-manager shortest_path.py provisioning_rest.py ryu.app.ofctl_rest ../rest_topology.py --observe-links
