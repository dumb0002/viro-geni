#include <stdint.h>
#include "checksum.h"

/**
 * Computes the UDP checksum based on the IP pseudo header and the UDP header
 * Returns the checksum value that should be written directly to the header
 */
uint16_t udp_sum_calc(uint16_t len_udp, uint16_t src_addr[],
                       uint16_t dest_addr[], uint16_t buff[]) {
  uint8_t proto_udp = 17; // tcp protocol number
  uint64_t sum;
  int nleft;
  uint16_t *w;

  sum = 0;
  nleft = len_udp;
  w = buff;

  /* calculate the checksum for the tcp header and payload */
  while(nleft > 1) {
    sum += *w++;
    nleft -= 2;
  }

  /* if nleft is 1 there ist still on byte left.
     We add a padding byte (0xFF) to build a 16bit word */
  if(nleft > 0) {
    /* sum += *w&0xFF; */
    sum += *w & ntohs(0xFF00); /* Thanks to Dalton */
  }

  /* add the pseudo header */
  sum += src_addr[0];
  sum += src_addr[1];
  sum += dest_addr[0];
  sum += dest_addr[1];
  sum += htons(len_udp);
  sum += htons(proto_udp);

  // keep only the last 16 bits of the 32 bit calculated sum and add
  // the carries
  sum = (sum >> 16) + (sum & 0xFFFF);
  sum += (sum >> 16);

  // Take the one's complement of sum
  sum = ~sum;

  return ((u_int16_t)sum);
}

/**
 * Computes the TCP checksum based on the IP pseudo header and the TCP header
 * Returns the checksum value that should be written directly to the header
 */
uint16_t tcp_sum_calc(uint16_t len_tcp, uint16_t src_addr[],
                       uint16_t dest_addr[], uint16_t buff[]) {
  uint8_t proto_tcp = 6; // tcp protocol number
  uint64_t sum;
  int nleft;
  uint16_t *w;

  sum = 0;
  nleft = len_tcp;
  w = buff;

  /* calculate the checksum for the tcp header and payload */
  while(nleft > 1) {
    sum += *w++;
    nleft -= 2;
  }

  /* if nleft is 1 there ist still on byte left.
     We add a padding byte (0xFF) to build a 16bit word */
  if(nleft > 0) {
    /* sum += *w&0xFF; */
    sum += *w & ntohs(0xFF00); /* Thanks to Dalton */
  }

  /* add the pseudo header */
  sum += src_addr[0];
  sum += src_addr[1];
  sum += dest_addr[0];
  sum += dest_addr[1];
  sum += htons(len_tcp);
  sum += htons(proto_tcp);

  // keep only the last 16 bits of the 32 bit calculated sum and add
  // the carries
  sum = (sum >> 16) + (sum & 0xFFFF);
  sum += (sum >> 16);

  // Take the one's complement of sum
  sum = ~sum;

  return ((u_int16_t)sum);
}

/**
 * Computes the IP header checksum given a pointer to the header start,
 * it assumes that the checksum field is set to zero before calling.
 * Returns the checksum value that should be written to the header
 */
uint16_t checksum(uint16_t *ptr, int len) {
  int sum = 0;
  uint16_t *w = ptr;

  int nleft = len;

  while(nleft > 1) {
    sum += *w++;
    nleft -= 2;
  }

  sum = (sum >> 16) + (sum & 0xFFFF);
  sum += (sum >> 16);

  return ~sum;
}

