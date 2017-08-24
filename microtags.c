/*
 * microtags: A lightweight C-based mechanism for time and event logging
 * on embedded systems 
 *
 * Copyright (C) 2017 Andreas Walz
 *
 * Author: Andreas Walz (andreas.walz@hs-offenburg.de)
 *
 * microtags is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of
 * the License, or (at your option) any later version.
 *
 * microtags is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with microtags; if not, see <http://www.gnu.org/licenses/>
 * or write to the Free Software Foundation, Inc., 51 Franklin Street,
 * Fifth Floor, Boston, MA 02110-1301, USA.
 */

#include "microtags.h"

#ifndef MICROTAGS_F_GET_TICKS
    #define MICROTAGS_F_GET_TICKS() microtags_get_ticks()
#endif

/* externally defined function to return current tick counter */
extern uint32_t MICROTAGS_F_GET_TICKS();

/* the counter holding the current number of microtags in the buffer */
static uint_fast16_t microtags_n_tags_in_buffer = 0;

/* the buffer to hold microtags between being set and being sent out */
static microtag_t* microtags_buffer = 0;

/* the length of the microtags buffer in units of one microtrag */
static int microtags_buffer_length_n_tags = 0;


/*
 * Function to set a ticks-based microtag, i.e. write a microtag to the buffer
 * ___________________________________________________________________________
 */
void microtags_init(microtag_t* buffer, int buffer_length_n_tags) {

    microtags_buffer = buffer;
    microtags_buffer_length_n_tags = buffer_length_n_tags;
}


/*
 * Function to set a ticks-based microtag, i.e. write a microtag to the buffer
 * ___________________________________________________________________________
 */
void microtags_set_with_ticks(uint_fast16_t id) {

#ifndef MICROTAGS_SKIP_LENGTH_CHECK
    /* buffer overflow protection */
    if (microtags_n_tags_in_buffer >= microtags_buffer_length_n_tags) {
        return;
    }
#endif

	/* store in memory */
	microtags_buffer[microtags_n_tags_in_buffer].data = MICROTAGS_F_GET_TICKS();
	microtags_buffer[microtags_n_tags_in_buffer++].id = id;
}


/*
 * Function to set a data-based microtag, i.e. write a microtag to the buffer
 * ___________________________________________________________________________
 */
void microtags_set_with_data(uint_fast16_t id, uint_fast32_t data) {

#ifndef MICROTAGS_SKIP_LENGTH_CHECK
    /* buffer overflow protection */
    if (microtags_n_tags_in_buffer >= microtags_buffer_length_n_tags) {
        return;
    }
#endif

	/* store in memory */
	microtags_buffer[microtags_n_tags_in_buffer].data = data;
	microtags_buffer[microtags_n_tags_in_buffer++].id = id;
}


/*
 * Function to send out all microtags from the buffer and clear the buffer
 * ___________________________________________________________________________
 */
void microtags_flush_text(microtags_f_send_byte_t microtags_f_send_byte) {

    /* array used to convert data to base64 */
	static const uint8_t microtags_base64[64] = {
			'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
            'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
            'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
            'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
            'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
            'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
            'w', 'x', 'y', 'z', '0', '1', '2', '3',
            '4', '5', '6', '7', '8', '9', '+', '/' };

	uint_fast32_t   data;
	uint_fast16_t   id;
	uint_fast16_t   i;
#ifdef MICROTAGS_TEXT_PREFIX
	const uint8_t*  c;
#endif

    if (microtags_f_send_byte == 0) {
        return;
    }

    /* iterate over all microtags in the buffer */
    for (i = 0; i < microtags_n_tags_in_buffer; ++i) {

#ifdef MICROTAGS_TEXT_PREFIX
        /* Send out a prefix before every microtag */
        c = MICROTAGS_TEXT_PREFIX;
        while (*c != 0) {
            (*microtags_f_send_byte)(*c);
            c++;
        }
#endif

        data = microtags_buffer[i].data;
        id = microtags_buffer[i].id;

        (*microtags_f_send_byte)(microtags_base64[
            /* most-significant bits of data ... */
            (data & 0xFC000000) >> 26]); 
        (*microtags_f_send_byte)(microtags_base64[
            (data & (0xFC000000 >> 6)) >> 20]); 
        (*microtags_f_send_byte)(microtags_base64[
            (data & (0xFC000000 >> 12)) >> 14]); 
        (*microtags_f_send_byte)(microtags_base64[
            (data & (0xFC000000 >> 18)) >> 8]); 
        (*microtags_f_send_byte)(microtags_base64[
            (data & (0xFC000000 >> 24)) >> 2]);
        (*microtags_f_send_byte)(microtags_base64[
            /* ... least-significant bits of data */
            ((data & (0xFC000000 >> 30)) << 4)
            /* most-significant bits of ID ... */
            | ((id & 0x0000F000) >> 12)]); 
        (*microtags_f_send_byte)(microtags_base64[
            (id & 0x00000FC0 >> 0) >> 6]); 
        (*microtags_f_send_byte)(microtags_base64[
            /* ... least-significant bits of ID */
            id & 0x00000FC0 >> 6]); 

        /* send out a newline */
	    (*microtags_f_send_byte)('\n');
    }

    /* clear the buffer */
    microtags_clear();
}


/*
 * Function to clear the buffer
 * ___________________________________________________________________________
 */
void microtags_clear(void) {

    microtags_n_tags_in_buffer = 0;
}

