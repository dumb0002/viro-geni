## GENI-VIRO Project

#### Software requirements

Open vSwitch requirements
`sudo apt-get install libxml2-dev gcc-multilib`


#### Mininet Instructions
This section summarizes Mininet specific details such as running different topologies and connecting to Mininet hosts and switches.

##### Running VIRO Experiments
To run a VIRO experiment you need to create a topology file.
The topology file contains one edge per line.
For example, to create a linear topology with three switches, the topology file <code>exp.txt</code> will look like this
```bash
1 2
2 3
```
Then, you can do the following to start Mininet
```bash
cd py/mininet
source env-vars.sh
sudo -E ./mininet-exp.py exp.txt
```
Mininet will start and create the linear toplogy in <code>exp.txt</code>. Each will be attached to one host and one local controller.
All switches will be connected to the remote controller. To change this behavior, you will need to change <code>mininet-exp.py</code> file.

Nodes will be named in the following form:
* Hosts: _h1_, _h2_, ...
* Switches: _s1_, _s2_, ...
* Local controllers: _c1_, _c2_, ...
* Remote controller: _remote_

Host _h1_ and local controller _c1_ will be connected to switch _s1_. Other hosts and local controller follow the same pattern.

##### Connecting to Nodes
Connecting to nodes in your Mininet experiment is very simple. For instance, to connect to _h1_ and run `ifconfig`
```bash
sudo ./node.sh h1
ifconfig
```

To disconnect from _h1_, use the keyboard shortcut `Ctrl+A D`

##### Open vSwitch
OVS source code is located under the `openvswitch` directory.
To start OVS, you need to run `./ovs.sh start` from inside the `openvswitch` direcotry.
The `ovs.sh` file has other useful commands to install and uninstall OVS to a raw VM.
For example, `./ovs.sh install` will install `openvswitch` to the new VM. 

##### Controllers
Controller log files are located under the `tmp` directory with the name of each controller.
For example, local controller 1 log file "_c1_" is located in `/tmp/c1.log`

To start the remote controller outside of Mininet, you just need to run the following command on the machine hosting the remote controller
```bash
./pox.py --verbose openflow.of_01 --port=6633 viro.core viro.remote.controller viro.remote.dhcpd viro.remote.arpd
```
To start the local controller on a VM hosting our VIRO OVS instance, you need to run
```bash
./pox.py --verbose openflow.of_01 --port=6634 viro.core viro.local.controller
```

##### Mininet Errors
To force Mininet to kill all controllers and hosts, you can run `sudo ./stop.sh` from inside `py/mininet` directory.
