#!/bin/bash

op=$1

umask 022

if [[ "$op" == "install" ]]; then
    ./boot.sh \
        && ./configure --with-linux=/lib/modules/`uname -r`/build \
        && make C=1 --quiet \
        && sudo make install \
        && sudo make modules_install \
        && sudo insmod datapath/linux/openvswitch.ko


	sudo rm /usr/local/etc/openvswitch/conf.db
    sudo mkdir -p /usr/local/etc/openvswitch
    sudo ovsdb-tool create /usr/local/etc/openvswitch/conf.db vswitchd/vswitch.ovsschema
elif [[ "$op" == "uninstall" ]]; then
    sudo kill `cd /usr/local/var/run/openvswitch && cat ovsdb-server.pid ovs-vswitchd.pid`

    sudo rmmod openvswitch
    make uninstall
    sudo rm -rf /usr/local/etc/openvswitch
elif [[ "$op" == "start" ]]; then
	./ovs.sh stop
    make C=1 --quiet && \
    	sudo make --quiet install && \
    	sudo make modules_install && \
        sudo insmod ./datapath/linux/openvswitch.ko && \
    	sudo ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock \
        	--remote=db:Open_vSwitch,Open_vSwitch,manager_options \
        	--private-key=db:Open_vSwitch,SSL,private_key \
        	--certificate=db:Open_vSwitch,SSL,certificate \
        	--bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert \
        	--pidfile --detach && \
    	sudo ovs-vsctl --no-wait init && \
    	sudo ovs-vswitchd --pidfile --detach
elif [[ "$op" == "stop" ]]; then
    sudo kill -9 `cd /usr/local/var/run/openvswitch && cat ovsdb-server.pid ovs-vswitchd.pid`
    sudo rmmod openvswitch
elif [[ "$op" == "stop-logging" ]]; then
    sudo ovs-appctl vlog/list | tail -n +3 | awk '{print $1}' | xargs -I{} ovs-appctl vlog/set {},file,off
    sudo ovs-appctl vlog/list | tail -n +3 | awk '{print $1}' | xargs -I{} ovs-appctl vlog/set {},syslog,off
else
    echo "Invalid operation."
fi
