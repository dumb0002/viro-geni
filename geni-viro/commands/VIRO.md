
##### Tutorials Websites 
Mininnet download http://mininet.org/download/
Mininet tutorial http://mininet.org/walkthrough/
OVS tutorial: http://wangcong.org/blog/archives/2131



##### Mininet Commands
I. to start Mininet:
    a) username: mininet
    b) password: mininet


II. to open a linux terminal with mininet
    a) on mininet vm: sudo dhclient eth1 (e.g: 192.168.56.101)
    b) on linux terminal: ssh -X mininet@192.168.56.101  (make sure to enable X11 forwarding)


III. to start mininet with different topologies:
    E.g:
       a) sudo mn -x --controller=remote,ip=127.0.0.1,port=6633 --topo linear,2
       b) sudo mn --controller=remote,ip=192.168.56.101,port=6633 -x    # start basic topology
       c) sudo mn --topo linear --switch ovsk --controller=remote,ip=192.168.56.101,port=6633 -x
       d) sudo /usr/local/bin/mn --switch ovsk --controller=remote --custom /home/mininet/source/diagFlow-topo-2host.py --topo DiagFlow --mac
    

   ***** commands to start mininet with user defined topologies ******
     E.g.:

        a) sudo mn --custom ~/mininet/custom/topo-2sw-2host.py --topo mytopo
        b) sudo mn --custom ~/mininet/viroExamples/viroTopology1.py --topo DiagFlow -x
        c) sudo mn --custom ~/mininet/viroExamples/viroTopology8.py --topo DiagFlow8 -x
   
    
IV. start POX controller with different modules
    E.g: 
       a) ./pox.py --no-cli viro_management
       b) ./pox.py log.level  --WARNING --openflow=DEBUG openflow.of_01 --port=6634  #start Pox
       c) ./pox.py log.level  --WARNING --openflow=DEBUG openflow.of_01 --port=6633 forwarding.l2_learning
       d) ./pox.py log.level  --WARNING --openflow=DEBUG openflow.of_01 --port=6633 forwarding.viro_updateController
       e) /pox.py log.level  --WARNING --openflow=DEBUG openflow.of_01 --port=6633 forwarding.viro_controller
       e) /pox.py --no-cli --port=6634 
       f) ./pox.py misc.dhcpd:default - start dhcp module



V. Others Mininets commands:
   E.g:
      a) h1 tcpdump -tt -nn -s0 -i h1-eth0 == command to use tcpdump at interface - eth0 in host h1
      b)  net == command to see the mininet topology (hows the information about interfaces and switches) 


    
##### OVS Commmands  
   
I. change switch dpid: 
     i) set dpid:  ovs-vsctl set bridge br0 other-config:datapath-id=xxx, eg: "0000000000000005"
     ii) get dpid:  ovs-vsctl get bridge br0 datapath_id
    
II.  connect the switch with multiple controllers: sudo ovs-vsctl set-controller br0 tcp:172.17.1.16:6633 \tcp:127.0.0.1:6634
     

III. gets switch fail mode: sudo ovs-vsctl get-fail-mode s1


IV. shows the features of the OVS switch: sudo ovs-ofctl show <switchname>. Eg: s1 or s2

V. add/remove/list the bridge to the switch: 

   E.g.
     a) Add: sudo ovs-vsctl add-br <bridgename>, Eg: br0, s1 or s2
     b) Delete: sudo ovs-vsctl del-br <bridgename>, Eg: br0, s1 or s2
     c) List: sudo ovs-vsctl list-br



##### Instructions to run VIRO in GENI

WARNING: do not add eth0 interface into the OVS

     a) Find the switch's interface connected to the controller:
         i) check the interface that has the same subnet address as the controller
         ii) don't add this inferface into the OVS, but uses its Ip address to set the IpAdress of the remote controller for the correspondent switch.

     b) sudo ifconfig ethX 0: remove the IP from the interfaces

     c) sudo ovs-vsctl add-port br0 ethX : add the interfaces to the switch

     d) sudo ovs-vsctl list-ports br0: list the interfaces connected to the bridge br0

     e) sudo ovs-vsctl set-controller: br0 tcp:172.17.1.16:6633 \tcp:127.0.0.1:6634

     f) sudo ovs-vsctl set-fail-mode br0 secure : set the fail mode of the switch to secure

     g) sudo ovs-vsctl show

     h) Start the remote controller:
         ./pox.py --verbose openflow.of_01 --port=6633 viro.core viro.remote.controller viro.remote.dhcpd viro.remote.arpd

     i) Start the local controller
         ./pox.py --verbose openflow.of_01 --port=6634 viro.core viro.local.controller


##### Instructions to connect a client or server in VIRO-GENI switch
      
     a) disable IpAddress from the client and server: sudo ifconfig eth1 0
     
     b) Request new IpAddress: sudo dhclient eth1

     c) Accelerate ARP requesting for both client and server (refresh ARP table): 
  
      == watch -n 3 sudo arping <ipAddress, eg: 192.168.0.2> -f -I ethX
        
     


















