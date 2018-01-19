#include "ipmi.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static FILE *f = NULL;

struct common_header *ch = NULL;
struct board_info_area *bia = NULL;
struct oem_record *oem = NULL;
struct internal_use_area *iua = NULL;

struct dc_load_list *dcll = NULL;
struct dc_output_list *dcol = NULL;

int ipmi_file_open(const char *name)
{
	if (f)
		fclose(f);
	f = fopen(name, "w");
	if (!f)
		return -1;
	return 0;
}

void ipmi_file_close(void)
{
	if (f)
		fclose(f);
}

uint8_t checksum(uint8_t *data, int len)
{
	int i;
	int sum = 0;

	for (i = 0; i < len; i++)
		sum += data[i];

	return (-sum)&0xff;
}

int board_info_area_get_size(uint8_t *pad)
{
	int size = 13 +
		(bia->mfgr_typelen & 0x3f) +
		(bia->product_typelen & 0x3f) +
		(bia->serial_typelen & 0x3f) +
		(bia->partnum_typelen & 0x3f) +
		(bia->fru_fid_typelen & 0x3f);
	if (size & 0x7) {
		if (pad) {
			*pad = 8 - (size & 0x7);
		}
		size -= size % 8;
		size += 8;
	}
	return size;
}

int internal_use_area_get_size(void)
{
	return 1 + iua->len;
}

int ipmi_common_header_write(void)
{
	int ret;

	if (!ch || !f)
		return -1;

	ch->checksum = checksum((uint8_t *)ch, sizeof(struct common_header) - 1);
	ret = fwrite(ch, 1, sizeof(struct common_header), f);

	return 0;
}

void ipmi_set_board_info_area(struct board_info_area *d)
{
	bia = d;
}

void ipmi_add_dc_load_record(struct dc_load_record *d)
{
	struct dc_load_list *l = malloc(sizeof(struct dc_load_list));
	l->rec = d;
	l->next = NULL;
	if (!dcll) {
		dcll = l;
	} else {
		l->next = dcll;
		dcll = l;
	}
}

void ipmi_add_dc_output_record(struct dc_output_record *d)
{
	struct dc_output_list *l = malloc(sizeof(struct dc_output_list));
	l->rec = d;
	l->next = NULL;
	if (!dcol) {
		dcol = l;
	} else {
		l->next = dcol;
		dcol = l;
	}
}

void ipmi_set_oem_record(struct oem_record *d)
{
	oem = d;
}

int ipmi_board_info_area_write(void)
{
	int i;
	int len;
	int ret;
	uint8_t pad = 0;
	uint8_t checksum;

	if (!bia || !f)
		return -1;

	/* Write upto the mfgr_data */
	ret = fwrite(bia, 6, 1, f);

	len = bia->mfgr_typelen & 0x3f;
	ret = fwrite(&bia->mfgr_typelen, 1, sizeof(uint8_t), f);
	ret = fwrite(bia->mfgr_data, len, 1, f);

	len = bia->product_typelen & 0x3f;
	ret = fwrite(&bia->product_typelen, 1, sizeof(uint8_t), f);
	ret = fwrite(bia->product_data, len, 1, f);

	len = bia->serial_typelen & 0x3f;
	ret = fwrite(&bia->serial_typelen, 1, sizeof(uint8_t), f);
	ret = fwrite(bia->serial_data, len, 1, f);

	len = bia->partnum_typelen & 0x3f;
	ret = fwrite(&bia->partnum_typelen, 1, sizeof(uint8_t), f);
	ret = fwrite(bia->partnum_data, len, 1, f);

	len = bia->fru_fid_typelen & 0x3f;
	ret = fwrite(&bia->fru_fid_typelen, 1, sizeof(uint8_t), f);
	ret = fwrite(bia->fru_fid_data, len, 1, f);

        bia->typelen_end = 0xc1;
        ret = fwrite(&bia->typelen_end, 1, sizeof(uint8_t), f);

	/* calculate checksum here */
	checksum = 0;
	checksum +=
		bia->format +
		bia->area_len +
		bia->language +
		bia->mfg_date0 +
		bia->mfg_date1 +
		bia->mfg_date2 +
		bia->mfgr_typelen +
		bia->product_typelen +
		bia->serial_typelen +
		bia->partnum_typelen +
		bia->fru_fid_typelen +
		bia->typelen_end;

	for (i = 0; i < (bia->mfgr_typelen & 0x3f); i++)
		checksum += bia->mfgr_data[i];

	for (i = 0; i < (bia->product_typelen & 0x3f); i++)
		checksum += bia->product_data[i];

	for (i = 0; i < (bia->serial_typelen & 0x3f); i++)
		checksum += bia->serial_data[i];

	for (i = 0; i < (bia->partnum_typelen & 0x3f); i++)
		checksum += bia->partnum_data[i];

	for (i = 0; i < (bia->fru_fid_typelen & 0x3f); i++)
		checksum += bia->fru_fid_data[i];

	checksum = -checksum;
	checksum &= 0xff;
	bia->checksum = checksum;

	uint8_t nul = 0;
	board_info_area_get_size(&pad);
	for (i = 0; i < pad; i++)
		ret = fwrite(&nul, 1, sizeof(uint8_t), f);
	ret = fwrite(&bia->checksum, 1, sizeof(uint8_t), f);

	return 0;
}

int ipmi_dc_load_record_write(int end)
{
	int ret;
	struct dc_load_list *t;

	if (!dcll || !f)
		return -1;

	t = dcll;
	while (t) {
		struct multirecord_header head;
		head.record_typeid = 0x2;	/* DC load type */
		head.extra = 0x2;
		if (end)
			head.extra |= (1 << 7);
		head.record_len = 13;
		head.record_checksum = checksum((uint8_t *)t->rec,
				sizeof(struct dc_load_record));
		head.header_checksum = checksum((uint8_t *)&head,
				sizeof(struct multirecord_header) - 1);

		ret = fwrite(&head, 1, sizeof(struct multirecord_header), f);
                ret = fwrite(&t->rec->voltage_required, 1, 1, f);
		ret = fwrite(&t->rec->nominal_voltage, 1, 12, f);
		t = t->next;
	}

	return 0;
}

int ipmi_dc_output_record_write(int end)
{
	int ret;
	struct dc_output_list *t;

	if (!dcol || !f)
		return -1;

	t = dcol;
	while (t) {
		struct multirecord_header head;
		head.record_typeid = 0x1;	/* DC output type */
		head.extra = 0x2;
		if (end)
			head.extra |= (1 << 7);
		head.record_len = 13;
		head.record_checksum = checksum((uint8_t *)t->rec,
				sizeof(struct dc_output_record));
		head.header_checksum = checksum((uint8_t *)&head,
				sizeof(struct multirecord_header) - 1);

		ret = fwrite(&head, 1, sizeof(struct multirecord_header), f);
		ret = fwrite(&t->rec->output_info, 1, 1, f);
                ret = fwrite(&t->rec->nominal_voltage, 1, 12, f);
		t = t->next;
	}

	return 0;
}

int ipmi_oem_record_write(int end)
{
	int ret;
	struct multirecord_header head;

	if (!oem || !f)
		return -1;

	/* VITA ID: 0x0012a2 (LS Byte first) */
	oem->mfg_id0 = 0xa2;
	oem->mfg_id1 = 0x12;
	oem->mfg_id2 = 0x00;

	head.record_typeid = 0xfa;	/* OEM record type */
	head.extra = 0x2;
	if (end)
		head.extra |= (1 << 7);
	head.record_len = sizeof(struct oem_record);
	head.record_checksum = checksum((uint8_t *)oem,
		sizeof(struct oem_record));
	head.header_checksum = checksum((uint8_t *)&head,
		sizeof(struct multirecord_header) - 1);

	ret = fwrite(&head, 1, sizeof(struct multirecord_header), f);
	ret = fwrite(oem, 1, sizeof(struct oem_record), f);

	return 0;
}

int multirecord_area_get_size(int *diff)
{
	struct dc_load_list *l1 = dcll;
	struct dc_output_list *l2 = dcol;
	int sum = 0;
	while (l1) {
		sum += sizeof(struct multirecord_header);
		sum += 13;
		l1 = l1->next;
	}
	while (l2) {
		sum += sizeof(struct multirecord_header);
		sum += 13;
		l2 = l2->next;
	}
	sum += sizeof(struct multirecord_header) + sizeof(struct oem_record);
	if (sum % 8) {
		if (diff) {
			*diff = 8 - (sum % 8);
		}
		sum += 8;
		sum &= ~7;
	}
	return sum;
}

int ipmi_write(void)
{
	int pad = 0;
	int padlen = 0;

	ch = malloc(sizeof(struct common_header));
	memset(ch, 0, sizeof(struct common_header));
        ch->format = 1; // Format version

        /*
         * IPMI areas arrangement in memory
         *
         * +------------------------------+
         * | Common header                |
         * +------------------------------+
         * | Board area                   |
         * +------------------------------+
         * | Multi-record area            |
         * |     +------------------------+
         * |     | 3x DC load records     |
         * |     +------------------------+
         * |     | 3x DC output records   |
         * |     +------------------------+
         * |     | OEM record             |
         * +-----+------------------------+
         * | Internal use area (optional) |
         * +------------------------------+
         */

        // Compute area offsets
	ch->board_area_off = sizeof(struct common_header)/8; // always 1
	ch->multirecord_off = (sizeof(struct common_header) + board_info_area_get_size(NULL))/8;
        if (iua)
                ch->internal_use_off = (sizeof(struct common_header) + board_info_area_get_size(NULL) + multirecord_area_get_size(NULL))/8;
        else
                ch->internal_use_off = 0;

        // Write common heade
	ipmi_common_header_write();

        // Write board info area, padding (to 8 byte multiple) is done inside the write function
        bia->area_len = board_info_area_get_size(NULL)/8;
	ipmi_board_info_area_write();

        // Write multi-record area
	ipmi_dc_load_record_write(0);
	ipmi_dc_output_record_write(0);
	ipmi_oem_record_write(1);

        // Padding after multi-record area
	multirecord_area_get_size(&padlen);
	if (padlen) {
		int i;
		for (i = 0; i < padlen; i++)
			fwrite(&pad, 1, 1, f);
	}

        // Write Internal Use area, if exists
        if (iua)
                ipmi_internal_use_area_write();

	return 0;
}

void ipmi_set_internal_use_area(struct internal_use_area *d)
{
	iua = d;
}

int ipmi_internal_use_area_write(void)
{
	if (!iua || !f)
		return -1;

	fwrite(&iua->format, 1, 1, f);
	fwrite(&iua->len, 1, 4, f);
	fwrite(iua->data, 1, iua->len, f);

	return 0;
}

unsigned char *ipmi_get_internal_use_data(char *data, int *l)
{
	unsigned char *buf;
	struct common_header *ch = (struct common_header *)data;
	unsigned char *d = (unsigned char *)data + ch->internal_use_off*8;
	int len = (int)d[1];
	buf = malloc(sizeof(uint8_t) * (len + 1));
	memcpy(buf, d+5, len);
	buf[len] = 0;
	*l = len;
	return buf;
}

int ipmi_get_mfg_date(char *data)
{
	int i;
	int ret = 0;
	struct common_header *ch = (struct common_header *)data;
	unsigned char *date = (unsigned char *)data + ch->board_area_off*8 + 3;
	for (i = 0; i < 3; i++)
		ret |= (date[i] << (i*8));
	return ret;
}
