#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netpacket/packet.h>
#include <net/ethernet.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <netinet/ether.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <netinet/in.h>
#include <net/if.h>
#include <unistd.h>
#include <pcap.h>
#include <pcap/pcap.h>
#include <stdbool.h>
#include <stdint.h>
#include <signal.h>
#include <linux/kernel.h>

#include "checksum.h"

#define SNAP_LEN 65535
#define BUF_SIZE 1024

#define ETH_P_VIRO  0x0802

#define VIRO_SRC_SW        htonl(0x02)
#define VIRO_SRC_HOST      htons(0x01)
#define VIRO_DST_SW        htonl(0x03)
#define VIRO_DST_HOST      htons(0x01)
#define VIRO_FD_SW         htonl(0x0a)
#define VIRO_FD_HOST       htons(0x0b)

#define VIRO_HDR_LEN       8
#define VIRO_ETH_HDR_LEN   22

#define IP_HDR_LEN         sizeof(struct iphdr)
#define UDP_HDR_LEN        sizeof(struct udphdr)

#define NW_SRC "192.168.1.10"
#define NW_DST "192.168.1.20"
#define TP_SRC 8888
#define TP_DST 9999

struct viro_addr {
	__be32 sw;
	__be16 host;
} __attribute__((packed));

static struct viro_addr VIRO_SRC, VIRO_DST;

struct viro_hdr {
    __be32 fd_sw;
    __be16 fd_host;
    __be16 eth_next_type;
} __attribute__((packed));

struct viro_eth_hdr {
    uint8_t eth_dst[ETHER_ADDR_LEN];
    uint8_t eth_src[ETHER_ADDR_LEN];
    __be16 eth_type;
    __be32 fd_sw;
    __be16 fd_host;
    __be16 eth_next_type;
} __attribute__((packed));

union ipaddr {
	u_int32_t addr;
	u_int8_t bytes[4];
};

struct netiface {
	int index;
	char name[IF_NAMESIZE];
	uint8_t mac[ETHER_ADDR_LEN];
	union ipaddr ipaddr;
};

void print_netiface(struct netiface *iface) {
	uint8_t *hw = iface->mac;
	printf("Network Interface:\n");
	printf("NAME = %s\n", iface->name);
	printf("MAC = %02x.%02x.%02x.%02x.%02x.%02x\n",
			hw[0], hw[1], hw[2], hw[3], hw[4], hw[5]);

	union ipaddr ip;
	ip.addr = ntohl(iface->ipaddr.addr);
	printf("IP = %03d.%03d.%03d.%03d\n",
			ip.bytes[0], ip.bytes[1], ip.bytes[2], ip.bytes[3]);
}

void add_ethernet_header(struct ether_header *eth) {
	memcpy(eth->ether_dhost, &VIRO_DST, ETHER_ADDR_LEN);
	memcpy(eth->ether_shost, &VIRO_SRC, ETHER_ADDR_LEN);
	eth->ether_type = htons(ETH_P_IP);
}

void add_viro_ethernet_header(struct viro_eth_hdr *ve) {
	uint8_t *addr;
	addr = &VIRO_DST;
	memcpy(ve->eth_dst, addr, ETHER_ADDR_LEN);

	addr = &VIRO_SRC;
	memcpy(ve->eth_src, addr, ETHER_ADDR_LEN);

	ve->eth_type = htons(ETH_P_VIRO);

	ve->fd_sw = VIRO_FD_SW;
	ve->fd_host = VIRO_FD_HOST;

	ve->eth_next_type = htons(ETH_P_IP);
}

void add_ip_header(struct iphdr *iph, int payload_len) {
	iph->ihl = 5;
	iph->version = 4;
	iph->tos = 0;
	iph->tot_len = htons(IP_HDR_LEN + payload_len);
	iph->id = htons(12345);
	iph->frag_off = 0;
	iph->ttl = 64;
	iph->protocol = IPPROTO_UDP;
	iph->check = 0;

	struct sockaddr_in sa;
	inet_pton(AF_INET, NW_SRC, &(sa.sin_addr));
	iph->saddr = sa.sin_addr.s_addr;
	inet_pton(AF_INET, NW_DST, &(sa.sin_addr));
	iph->daddr = sa.sin_addr.s_addr;
}

void add_udp_header(struct udphdr *udph, int payload_len) {
	udph->source = htons(TP_SRC);
	udph->dest = htons(TP_DST);
	udph->len = htons(UDP_HDR_LEN + payload_len);
	udph->check = 0;
}

void add_payload(char *payload, char *msg, int l) {
	memcpy(payload, &l, sizeof(int));
	payload += sizeof(int);
	memcpy(payload, msg, l);
}

void print_packet(uint8_t *packet, int len) {
	int i = 0;
	int lw = 16;

	for(i = 0; i < len; i+=2) {
		printf(" %02x%02x", packet[i], packet[i+1]);

		if(i > 0 && i % lw == 0)
			printf("\n");
	}

	printf("\n\n");
}

void compute_checksums(struct iphdr *iph, struct udphdr *udph) {
  uint16_t *ptr = (uint16_t*) iph;
  iph->check = 0;
  iph->check = checksum(ptr, iph->ihl * 4);

  uint32_t datalen = ntohs(iph->tot_len) - iph->ihl * 4;

  udph->check = 0;
  udph->check = udp_sum_calc(datalen, (uint16_t*)&iph->saddr, (uint16_t*)&iph->daddr, (uint16_t*)udph);
}

void send_pkts_on_iface(struct netiface *iface, char *msg, int npkts, bool is_viro) {
	int i, sock, msg_len, payload_len;
	struct sockaddr_ll addr;
	char sendbuf[BUF_SIZE];
	char *packet;

	struct ether_header *eth;
	struct viro_eth_hdr *vehdr;
	struct iphdr *iphdr;
	struct udphdr *udphdr;

	msg_len = strlen(msg);
	payload_len = msg_len + sizeof(int); // 4-bytes to add message length to the payload

	memset(sendbuf, 0, BUF_SIZE);

	packet = sendbuf;

	if (is_viro) {
		vehdr = packet;
		add_viro_ethernet_header(vehdr);
		packet += VIRO_ETH_HDR_LEN;
	} else {
		eth = packet;
		add_ethernet_header(eth);
		packet += ETHER_HDR_LEN;
	}

	iphdr = packet;
	add_ip_header(iphdr, UDP_HDR_LEN + payload_len);
	packet += IP_HDR_LEN;

	udphdr = packet;
	add_udp_header(udphdr, payload_len);
	packet += UDP_HDR_LEN;

	add_payload(packet, msg, msg_len);
	packet += payload_len;

	compute_checksums(iphdr, udphdr);

	int tx_len = packet - sendbuf;

	printf("sending packets\n");

	if ((sock = socket(AF_PACKET, SOCK_RAW, IPPROTO_RAW)) == -1) {
		perror("socket");
		exit(EXIT_FAILURE);
	}

	addr.sll_halen = ETHER_ADDR_LEN;
	addr.sll_ifindex = iface->index;
	memcpy(addr.sll_addr, &VIRO_DST, ETHER_ADDR_LEN);

	size_t bytes;
	for (i = 0; i < npkts; i++) {
		bytes = sendto(sock, sendbuf, tx_len, 0, (struct sockaddr*) &addr, sizeof(struct sockaddr_ll));
		if (bytes < 0)
			fprintf(stderr, "sendto failed\n");
	}

	printf("done sending packets\n");
}

void get_iface_by_name(char *eth_name, struct netiface *iface) {
	struct if_nameindex *if_names, *ifn;
	struct ifreq ifr;
	struct netif *netifaces;
	int if_count, i, sock;

	memset(&ifr, 0x0, sizeof(struct ifreq));
	sock = socket(PF_INET, SOCK_DGRAM, 0);

	strcpy(ifr.ifr_name, eth_name);
	strcpy(iface->name, eth_name);

	ioctl(sock, SIOCGIFINDEX, &ifr);
	iface->index = ifr.ifr_ifindex;

	ioctl(sock, SIOCGIFHWADDR, &ifr);
	memcpy(iface->mac, ifr.ifr_hwaddr.sa_data, ETH_ALEN);

	ioctl(sock, SIOCGIFADDR, &ifr);
	if (ifr.ifr_addr.sa_family == AF_INET) {
		memcpy(iface->ipaddr.bytes, ifr.ifr_addr.sa_data + 2, 4);
	} else {
		iface->ipaddr.addr = 0;
	}

	close(sock);
}

int main(int argc, char *argv[]) {
	char *proto = argv[1];
	char *iface_name = argv[2];
	char *msg = argv[3];
	int npkts = atoi(argv[4]);
	struct netiface iface;

	bool is_viro = true;
	if (strcmp(proto, "viro") != 0)
		is_viro = false;

	VIRO_SRC.sw = VIRO_SRC_SW;
	VIRO_SRC.host = VIRO_SRC_HOST;
	VIRO_DST.sw = VIRO_DST_SW;
	VIRO_DST.host = VIRO_DST_HOST;

	get_iface_by_name(iface_name, &iface);
	send_pkts_on_iface(&iface, msg, npkts, is_viro);

	return 0;
}
