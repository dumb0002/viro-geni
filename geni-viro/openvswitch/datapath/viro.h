#ifndef VIRO_H
#define VIRO_H 1

#include <linux/if_ether.h>
#include <linux/types.h>

#define VIRO_ETH_HDR_LEN 22
#define VIRO_HDR_LEN 8
#define ETH_P_VIRO 0x0802

struct viro_addr {
	__be32 sw;
	__be16 host;
} __attribute__((packed));

struct viro_hdr {
    __be32 fd_sw;
    __be16 fd_host;
    __be16 eth_next_type;
} __attribute__((packed));

struct viro_eth_hdr {
    unsigned char eth_dst[ETH_ALEN];
    unsigned char eth_src[ETH_ALEN];
    __be16 eth_type;
    __be32 fd_sw;
    __be16 fd_host;
    __be16 eth_next_type;
} __attribute__((packed));

struct viro_eth_vid_hdr {
	__be32 dst_sw;
	__be16 dst_host;
	__be32 src_sw;
	__be16 src_host;
    __be16 eth_type;
    __be32 fd_sw;
    __be16 fd_host;
    __be16 eth_next_type;
} __attribute__((packed));

#endif
