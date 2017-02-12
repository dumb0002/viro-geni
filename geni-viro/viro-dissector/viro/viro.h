#ifndef VIRO_H
#define VIRO_H 1

#ifdef __KERNEL__
#include <linux/types.h>
#else
#include <stdint.h>
#endif

#ifndef ETH_ALEN
#define ETH_ALEN 6
#endif

#define VIRO_ETH_HDR_LEN 22
#define VIRO_HDR_LEN 8
#define ETH_P_VIRO 0x0802

struct viro_hdr {
    uint32_t fd_sw;
    uint16_t fd_host;
    uint16_t eth_next_type;
} __attribute__((packed));

struct viro_eth_hdr {
    uint8_t eth_dst[ETH_ALEN];
    uint8_t eth_src[ETH_ALEN];
    uint16_t eth_type;
    uint32_t fd_sw;
    uint16_t fd_host;
    uint16_t eth_next_type;
} __attribute__((packed));

struct viro_eth_vid_hdr {
    uint32_t dst_sw;
    uint16_t dst_host;
    uint32_t src_sw;
    uint16_t src_host;
    uint16_t eth_type;
    uint32_t fd_sw;
    uint16_t fd_host;
    uint16_t eth_next_type;
} __attribute__((packed));

#endif
