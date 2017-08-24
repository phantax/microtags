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

#ifndef MICROTAGS_H_
#define MICROTAGS_H_

#include <stdint.h>


/* definition of a single microtag */
typedef struct {

    /* 32-bit data of the microtag */
    uint32_t data;

    /* 16-bit id of the microtag */
    uint16_t id;

} microtag_t;

/* definition of function pointer to send out a single byte */
typedef void (*microtags_f_send_byte_t)(uint8_t byte);

/* Function to init the microtags buffer */
void microtags_init(microtag_t* buffer, int buffer_length_n_tags);

/* Function to set a ticks-based microtag, i.e. write a microtag to the buffer */
void microtags_set_with_ticks(uint_fast16_t id);

/* Function to set a data-based microtag, i.e. write a microtag to the buffer */
void microtags_set_with_data(uint_fast16_t id, uint_fast32_t data);

/* Function to send out all microtags from the buffer and clear the buffer */
void microtags_flush_text(microtags_f_send_byte_t microtags_f_send_byte);

/* Function to clear the buffer */
void microtags_clear(void);


#endif
