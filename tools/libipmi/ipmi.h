#ifndef IPMI_H
#define IPMI_H

#include <stdint.h>
#include <stdio.h>

/* 8 bytes */
struct common_header {
	uint8_t format;
	uint8_t internal_use_off;
	uint8_t chassis_info_off;
	uint8_t board_area_off;
	uint8_t product_area_off;
	uint8_t multirecord_off;
	uint8_t pad;
	uint8_t checksum;
};

struct board_info_area {
	uint8_t format;
	uint8_t area_len;
	uint8_t language;
	uint8_t mfg_date0;
	uint8_t mfg_date1;
	uint8_t mfg_date2;

	uint8_t mfgr_typelen;
	uint8_t *mfgr_data;

	uint8_t product_typelen;
	uint8_t *product_data;

	uint8_t serial_typelen;
	uint8_t *serial_data;

	uint8_t partnum_typelen;
	uint8_t *partnum_data;

	uint8_t fru_fid_typelen;
	uint8_t *fru_fid_data;

/*	uint8_t *custom; */
	uint8_t typelen_end;

	uint8_t pad_len;
	uint8_t checksum;
};

/* 5 bytes */
struct multirecord_header {
	uint8_t record_typeid;
	uint8_t extra;
	uint8_t record_len;
	uint8_t record_checksum;
	uint8_t header_checksum;
};

struct dc_output_list {
	struct dc_output_record *rec;
	struct dc_output_list *next;
};

/* 13 bytes */
struct dc_load_record {
	uint8_t voltage_required;
	uint16_t nominal_voltage;
	uint16_t min_voltage;
	uint16_t max_voltage;
	uint16_t spec_ripple;
	uint16_t min_current;
	uint16_t max_current;
};

struct dc_load_list {
	struct dc_load_record *rec;
	struct dc_load_list *next;
};

/* 13 bytes */
struct dc_output_record {
	uint8_t output_info;
	uint16_t nominal_voltage;
	uint16_t max_neg_voltage_dev;
	uint16_t max_pos_voltage_dev;
	uint16_t ripple;
	uint16_t min_current_draw;
	uint16_t max_current_draw;
};

struct fmc_oem_data {
	uint8_t subtype_version;
	uint8_t other;
	uint8_t p1_a_nsig;
	uint8_t p1_b_nsig;
	uint8_t p2_a_nsig;
	uint8_t p2_b_nsig;
	uint8_t p1_p2_gbt_ntran;
	uint8_t max_clock;
};

/* 12 bytes */
struct oem_record {
	uint8_t mfg_id0;
	uint8_t mfg_id1;
	uint8_t mfg_id2;
	struct fmc_oem_data data;
};

struct internal_use_area {
	uint8_t format;
	int len;
	char *data;
};

int ipmi_file_open(const char *name);
void ipmi_file_close(void);
int ipmi_write(void);

int ipmi_common_header_write(void);

void ipmi_set_board_info_area(struct board_info_area *);
int ipmi_board_info_area_write(void);

void ipmi_set_internal_use_area(struct internal_use_area *);
int ipmi_internal_use_area_write(void);

void ipmi_add_dc_load_record(struct dc_load_record *);
int ipmi_dc_load_record_write(int);

void ipmi_add_dc_output_record(struct dc_output_record *);
int ipmi_dc_output_record_write(int);

void ipmi_set_oem_record(struct oem_record *);
int ipmi_oem_record_write(int);

unsigned char *ipmi_get_internal_use_data(char *data, int *l);
int ipmi_get_mfg_date(char *data);

#endif
