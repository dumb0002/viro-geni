\Architecture:          x86_64
CPU op-mode(s):        32-bit, 64-bit
Byte Order:            Little Endian
CPU(s):                1
On-line CPU(s) list:   0
Thread(s) per core:    1
Core(s) per socket:    1
Socket(s):             1
NUMA node(s):          1
Vendor ID:             GenuineIntel
CPU family:            6
Model:                 45
Stepping:              7
CPU MHz:               2095.010
BogoMIPS:              4190.02
Hypervisor vendor:     Xen
Virtualization type:   para
L1d cache:             32K
L1i cache:             32K
L2 cache:              256K
L3 cache:              20480K
NUMA node0 CPU(s):     0



01.demo-test.ch-geni-net.instageni.wisc.edu
    description: Computer
    width: 64 bits
    capabilities: vsyscall32
  *-core
       description: Motherboard
       physical id: 0
     *-memory
          description: System memory
          physical id: 0
          size: 489MiB
     *-cpu
          product: Intel(R) Xeon(R) CPU E5-2450 0 @ 2.10GHz
          vendor: Intel Corp.
          physical id: 1
          bus info: cpu@0
          width: 64 bits
          capabilities: fpu fpu_exception wp de tsc msr pae cx8 sep cmov pat clflush mmx fxsr sse sse2 ss ht syscall nx x86-64 constant_tsc up rep_good nopl pni pclmulqdq ssse3 cx16 sse4_1 sse4_2 x2apic popcnt tsc_deadline_timer aes xsave avx hypervisor lahf_lm ida arat epb xsaveopt pln pts dtherm
  *-network:0 DISABLED
       description: Ethernet interface
       physical id: 1
       logical name: tap0
       serial: 9e:73:7b:4c:65:32
       size: 10Mbit/s
       capabilities: ethernet physical
       configuration: autonegotiation=off broadcast=yes driver=tun driverversion=1.6 duplex=full firmware=N/A link=no multicast=yes port=twisted pair speed=10Mbit/s
  *-network:1 DISABLED
       description: Ethernet interface
       physical id: 2
       logical name: ovs-system
       serial: 72:6c:23:41:3f:36
       capabilities: ethernet physical
       configuration: broadcast=yes driver=openvswitch link=no multicast=yes
  *-network:2
       description: Ethernet interface
       physical id: 3
       logical name: br0
       serial: f6:8d:b9:13:b5:4a
       capabilities: ethernet physical
       configuration: broadcast=yes driver=openvswitch link=yes
  *-network:3
       description: Ethernet interface
       physical id: 4
       logical name: eth1
       serial: 02:28:7e:98:5f:f2
       capabilities: ethernet physical
       configuration: broadcast=yes driver=vif link=yes multicast=yes
  *-network:4
       description: Ethernet interface
       physical id: 5
       logical name: eth0
       serial: 02:99:ac:e0:14:2e
       capabilities: ethernet physical
       configuration: broadcast=yes driver=vif ip=128.104.159.146 link=yes multicast=yes
  *-network:5
       description: Ethernet interface
       physical id: 6
       logical name: tap1
       serial: 7a:16:6f:b0:4a:b5
       size: 10Mbit/s
       capabilities: ethernet physical
       configuration: autonegotiation=off broadcast=yes driver=tun driverversion=1.6 duplex=full firmware=N/A link=yes multicast=yes port=twisted pair speed=10Mbit/s


