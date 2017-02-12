#ifndef OPENFLOW_VIRO_EXT_H
#define OPENFLOW_VIRO_EXT_H 1

#include "openflow/openflow.h"
#include "openvswitch/types.h"
#include "openflow/nicira-ext.h"

#define VIRO_VENDOR_ID 0x00002323

#define VIRO_ET_VENDOR 0xb0c9

enum viro_vendor_code {
    VIRO_VC_VENDOR_ERROR  /* 'data' contains struct viro_vendor_error. */
};

/* 'data' for 'type' == VIRO_ET_VENDOR, 'code' == VIRO_VC_VENDOR_ERROR. */
struct viro_vendor_error {
    ovs_be32 vendor;            /* Vendor ID as in struct ofp_vendor_header. */
    ovs_be16 type;              /* Vendor-defined type. */
    ovs_be16 code;              /* Vendor-defined subtype. */
    /* Followed by at least the first 64 bytes of the failed request. */
};

/* viro vendor requests and replies. */

/* Header for viro vendor requests and replies. */
struct viro_header {
    struct ofp_header header;
    ovs_be32 vendor;            /* VIRO_VENDOR_ID. */
    ovs_be32 subtype;           /* See the NXT numbers in ofp-msgs.h. */
};
OFP_ASSERT(sizeof(struct viro_header) == 16);


/* viro vendor flow actions. */

enum viro_action_subtype {
    VIRO_AST_PUSH_FD,
    VIRO_AST_POP_FD,

    VIRO_AST_SET_VID_SW_FD,
    VIRO_AST_SET_VID_SW_SRC,
    VIRO_AST_SET_VID_SW_DST,

    VIRO_AST_SET_VID_HOST_FD,
    VIRO_AST_SET_VID_HOST_SRC,
    VIRO_AST_SET_VID_HOST_DST
};

/* Header for viro-defined actions. */
struct viro_action_header {
    ovs_be16 type;                  /* OFPAT_VENDOR. */
    ovs_be16 len;                   /* Length is 16. */
    ovs_be32 vendor;                /* VIRO_VENDOR_ID. */
    ovs_be16 subtype;               /* VIRO_AST_*. */
    uint8_t pad[6];
};
OFP_ASSERT(sizeof(struct viro_action_header) == 16);


struct viro_action_push_fd {
    ovs_be16 type;                  /* OFPAT_VENDOR. */
    ovs_be16 len;                   /* Length is 16. */
    ovs_be32 vendor;                /* VIRO_VENDOR_ID. */
    ovs_be16 subtype;               /* VIRO_AST_PUSH_FD. */
    ovs_be16 fd_host;
    ovs_be32 fd_sw;
};
OFP_ASSERT(sizeof(struct viro_action_push_fd) == 16);

struct viro_action_vid_sw {
    ovs_be16 type;                  /* OFPAT_VENDOR. */
    ovs_be16 len;                   /* Length is 16. */
    ovs_be32 vendor;                /* VIRO_VENDOR_ID. */
    ovs_be16 subtype;               /* VIRO_AST_VID_SW_* */
    uint8_t pad[2];
    ovs_be32 sw;
};
OFP_ASSERT(sizeof(struct viro_action_push_fd) == 16);

struct viro_action_vid_host {
    ovs_be16 type;                  /* OFPAT_VENDOR. */
    ovs_be16 len;                   /* Length is 16. */
    ovs_be32 vendor;                /* VIRO_VENDOR_ID. */
    ovs_be16 subtype;               /* VIRO_AST_VID_HOST_* */
    ovs_be16 host;
    uint8_t pad[4];
};
OFP_ASSERT(sizeof(struct viro_action_push_fd) == 16);


/* VIRO field extension to nicira exnteded matching
 * Only vids are maskable. Host Ids are not maskable
 */
#define NXM_VIRO_DST_SW       NXM_HEADER  (0x0002, 1, 4)
#define NXM_VIRO_DST_SW_W     NXM_HEADER_W(0x0002, 1, 4)
#define NXM_VIRO_DST_HOST     NXM_HEADER  (0x0002, 2, 2)
#define NXM_VIRO_SRC_SW       NXM_HEADER  (0x0002, 3, 4)
#define NXM_VIRO_SRC_SW_W     NXM_HEADER_W(0x0002, 3, 4)
#define NXM_VIRO_SRC_HOST     NXM_HEADER  (0x0002, 4, 2)
#define NXM_VIRO_FD_SW        NXM_HEADER  (0x0002, 5, 4)
#define NXM_VIRO_FD_SW_W      NXM_HEADER_W(0x0002, 5, 4)
#define NXM_VIRO_FD_HOST      NXM_HEADER  (0x0002, 6, 2)


#endif /* openflow/viro-ext.h */
