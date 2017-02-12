/** the version of viro this dissector was written for */
#define DISSECTOR_VIRO_MIN_VERSION 0x00
#define DISSECTOR_VIRO_MAX_VERSION 0x01
#define DISSECTOR_VIRO_VERSION_DRAFT_THRESHOLD 0x01

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include <stdio.h>
#include <stdlib.h>
#include <glib.h>
#include <epan/emem.h>
#include <epan/packet.h>
#include <epan/proto.h>
#include <epan/prefs.h>
#include <epan/etypes.h>
#include <string.h>
#include <arpa/inet.h>
#include <inttypes.h>
#include <viro.h>

#define SW_FMT "%02"PRIx32":%02"PRIx32":%02"PRIx32":%02"PRIx32
#define SW_ARGS(sw)                             \
    ntohl(sw) >> 24,                            \
    (ntohl(sw) >> 16) & 0xff,                   \
    (ntohl(sw) >> 8) & 0xff,                    \
    ntohl(sw) & 0xff

#define HOST_FMT "%02"PRIx16":%02"PRIx16
#define HOST_ARGS(host)                             \
    (ntohs(host) >> 8) & 0xff,                    \
    ntohs(host) & 0xff


/** if 0, padding bytes will not be shown in the dissector */
#define SHOW_PADDING 0

#define PROTO_TAG_VIRO  "VIRO"

/* Wireshark ID of the VIRO protocol */
static int proto_viro = -1;
static dissector_handle_t viro_handle;
static dissector_handle_t eth_handle;

//static dissector_table_t viro_dissector_table;

#define VIRO_TYPE_FILTER "eth.type"
static int global_viro_proto = VIRO_PROTO_NUM;


static int hf_viro_src_sw = -1;
static int hf_viro_src_host = -1;
static int hf_viro_dst_sw = -1;
static int hf_viro_dst_host = -1;
static int hf_viro_fd_sw = -1;
static int hf_viro_fd_host = -1;
static int hf_viro_eth_type = -1;
static int hf_viro_next_type = -1;
static int hf_viro_trailer = -1;
static gint ett_viro = -1;



static void dissect_viro(tvbuff_t *tvb, packet_info *pinfo, proto_tree *tree)
{
	guint16 eth_type;
	struct viro_eth_vid_hdr *vh;

	proto_tree *viro_tree = NULL;

	eth_type = tvb_get_ntohs(tvb, 12);

	if (eth_type != global_viro_proto) {
		call_dissector(eth_handle, tvb, pinfo, tree);
		return;
	}

	vh = (struct viro_eth_vid_hdr *) tvb_get_ptr(tvb, 0, sizeof *vh);

	col_set_str(pinfo->cinfo, COL_PROTOCOL, "VIRO");

	col_clear(pinfo->cinfo, COL_INFO);
	col_append_fstr(pinfo->cinfo, COL_INFO, "Forwarding Directive: "SW_FMT, SW_ARGS(vh->fd_sw));

	col_clear(pinfo->cinfo, COL_DEF_DST);
	col_clear(pinfo->cinfo, COL_DEF_SRC);

	col_append_fstr(pinfo->cinfo, COL_DEF_DST, SW_FMT, SW_ARGS(vh->dst_sw));
	col_append_fstr(pinfo->cinfo, COL_DEF_SRC, SW_FMT, SW_ARGS(vh->src_sw));


	if (tree) {

		proto_item *ti = NULL;
		ti = proto_tree_add_protocol_format(tree, proto_viro, tvb, 0, -1,
											"Viro Protocol, Src Switch: "SW_FMT", Src Host: "HOST_FMT
											", Dst Switch: "SW_FMT", Dst Host: "HOST_FMT
											", Forwarding Directive: "SW_FMT", Reserved: "HOST_FMT,
											SW_ARGS(vh->src_sw), HOST_ARGS(vh->src_host),
											SW_ARGS(vh->dst_sw), HOST_ARGS(vh->dst_host),
											SW_ARGS(vh->fd_sw), HOST_ARGS(vh->fd_host));

		viro_tree = proto_item_add_subtree(ti, ett_viro);

		proto_tree_add_uint_format(viro_tree, hf_viro_src_sw, tvb, 0, 4, vh->src_sw,
								   "Source Switch VID: "SW_FMT" (%"PRIu32")", SW_ARGS(vh->src_sw), ntohl(vh->src_sw));
		proto_tree_add_uint_format(viro_tree, hf_viro_src_host, tvb, 4, 2, vh->src_host,
								   "Source Host: "HOST_FMT" (%"PRIu16")", HOST_ARGS(vh->src_host), ntohs(vh->src_host));

		proto_tree_add_uint_format(viro_tree, hf_viro_dst_sw, tvb, 6, 4, vh->dst_sw,
								   "Destination Switch VID: "SW_FMT" (%"PRIu32")", SW_ARGS(vh->dst_sw), ntohl(vh->dst_sw));
		proto_tree_add_uint_format(viro_tree, hf_viro_dst_host, tvb, 10, 2, vh->dst_host,
								   "Destination Host: "HOST_FMT" (%"PRIu16")", HOST_ARGS(vh->dst_host), ntohs(vh->dst_host));

		proto_tree_add_item(viro_tree, hf_viro_eth_type, tvb, 12, 2, ENC_BIG_ENDIAN);

		proto_tree_add_uint_format(viro_tree, hf_viro_fd_sw, tvb, 14, 4, vh->fd_sw,
								   "Forwarding Directive VID: "SW_FMT" (%"PRIu32")", SW_ARGS(vh->fd_sw), ntohl(vh->fd_sw));
		proto_tree_add_uint_format(viro_tree, hf_viro_fd_host, tvb, 18, 2, vh->fd_host,
								   "Reserved Bytes: "HOST_FMT" (%"PRIu16")", HOST_ARGS(vh->fd_host), ntohs(vh->fd_host));

		ethertype(ntohs(vh->eth_next_type), tvb, VIRO_ETH_HDR_LEN, pinfo, tree, viro_tree, hf_viro_next_type, hf_viro_trailer, -1);
	}

}

void proto_register_viro()
{

	static hf_register_info hf[] = {
			{ &hf_viro_src_sw,
			{ "Source Switch VID", "viro.src_sw", FT_UINT32, BASE_HEX, NULL, 0x0, NULL, HFILL }},

			{ &hf_viro_src_host,
			{ "Source Host", "viro.src_host", FT_UINT16, BASE_HEX, NULL, 0x0, NULL, HFILL }},

			{ &hf_viro_dst_sw,
			{ "Destination Switch VID", "viro.dst_sw", FT_UINT32, BASE_HEX, NULL, 0x0, NULL, HFILL }},

			{ &hf_viro_dst_host,
			{ "Destination Host", "viro.dst_host", FT_UINT16, BASE_HEX, NULL, 0x0, NULL, HFILL }},

			{ &hf_viro_eth_type,
			{ "VIRO EtherType", "viro.eth_type", FT_UINT16, BASE_HEX, NULL, 0x0, NULL, HFILL }},

			{ &hf_viro_fd_sw,
			{ "Forwarding Directive VID", "viro.fd_sw", FT_UINT32, BASE_HEX, NULL, 0x0, NULL, HFILL }},

			{ &hf_viro_fd_host,
			{ "Reserved Bytes", "viro.fd_host", FT_UINT16, BASE_HEX, NULL, 0x0, NULL, HFILL }},

			{ &hf_viro_next_type,
			{ "Encapsulated EtherType", "viro.next_type", FT_UINT16, BASE_HEX, VALS(etype_vals), 0x0, NULL, HFILL }},

			{ &hf_viro_trailer,
			{ "Trailer", "viro.trailer", FT_BYTES, BASE_NONE, NULL, 0x0, NULL, HFILL }}
	};

   static gint *ett[] = {
		&ett_viro
	};

    proto_viro = proto_register_protocol("Viro Protocol", "VIRO", "viro");

    proto_register_field_array(proto_viro, hf, array_length(hf));
    proto_register_subtree_array(ett, array_length(ett));

    register_dissector("viro", dissect_viro, proto_viro);
}

void proto_reg_handoff_viro()
{
    eth_handle = find_dissector("eth");

    viro_handle = create_dissector_handle(dissect_viro, proto_viro);
    dissector_add_uint("wtap_encap", WTAP_ENCAP_ETHERNET, viro_handle);
}
