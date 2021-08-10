#include "microtags.h"
#include <stdio.h>

uint32_t microtags_get_ticks() {
    
    return 0;
}


void print_byte(uint8_t byte) {

    putc(byte, stdout);
}



int main(int argc , char *argv[]) {

    microtag_t microtags_buffer[1024];

    microtags_init(microtags_buffer, 1024);

    microtags_set_with_data(0x0001, 0x00000001);
    microtags_set_with_vardata(0x0120, "ABCDEFGHIJKLMNOP", 10);
    microtags_set_with_vardata(0x0121, "ABCDEFGHIJKLMNOP", 11);
    microtags_set_with_vardata(0x0122, "ABCDEFGHIJKLMNOP", 12);
    microtags_set_with_vardata(0x0123, "ABCDEFGHIJKLMNOP", 13);
    microtags_set_with_data(0x0002, 0x00000002);

    microtags_flush_text(print_byte);   

    return 0;
}




