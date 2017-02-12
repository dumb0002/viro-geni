#include <sys/types.h>
#include <netinet/in.h>

#ifndef __CHECKSUM_H__
#define __CHECKSUM_H__

// compute udp checksum
uint16_t udp_sum_calc(uint16_t len_udp, uint16_t src_addr[],
                       uint16_t dest_addr[], uint16_t buff[]);

// compute tcp checksum
uint16_t tcp_sum_calc(uint16_t len_tcp, uint16_t src_addr[],
                       uint16_t dest_addr[], uint16_t buff[]);

// compute ip checksum
uint16_t checksum(uint16_t *ptr, int len);

#endif
