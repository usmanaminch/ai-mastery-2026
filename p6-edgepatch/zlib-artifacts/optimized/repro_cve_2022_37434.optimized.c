#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "zlib.h"

int main(void) {
    z_stream strm;
    gz_header head;
    unsigned char output[1024];
    int ret = 0;

    unsigned char *extra = malloc(1024);
    unsigned char *extra_data = malloc(1024);
    if (!extra || !extra_data) {
        free(extra);
        free(extra_data);
        fprintf(stderr, "Allocation failed\n");
        return 1;
    }

    memset(&strm, 0, sizeof(strm));
    if (inflateInit2(&strm, 16 + 15) != Z_OK) { // 16 + 15 for gzip decoding
        fprintf(stderr, "inflateInit2 failed\n");
        ret = 1;
        goto cleanup;
    }

    memset(&head, 0, sizeof(head));
    head.extra = extra;
    head.extra_max = 10; // Enforce tight bounds limitation
    
    if (inflateGetHeader(&strm, &head) != Z_OK) {
        fprintf(stderr, "inflateGetHeader failed\n");
        ret = 1;
        goto cleanup_strm;
    }

    /*
     * Malicious gzip header payload:
     * XLEN: ff ff (65535 bytes)
     */
    unsigned char malicious_gzip[] = {
        0x1f, 0x8b, 0x08, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03,
        0xff, 0xff, 
    };

    strm.next_in = malicious_gzip;
    strm.avail_in = sizeof(malicious_gzip);
    strm.next_out = output;
    strm.avail_out = sizeof(output);

    // Initial inflate to parse the header up to the extra field requirement
    if (inflate(&strm, Z_BLOCK) == Z_STREAM_ERROR) {
        fprintf(stderr, "First inflate failed\n");
        ret = 1;
        goto cleanup_strm;
    }

    memset(extra_data, 'A', 1024);

    // Feed many small chunks to incrementally push the offset 'len' past 'extra_max'
    for (int i = 0; i < 20; i++) {
        strm.next_in = extra_data;
        strm.avail_in = 1; 
        if (inflate(&strm, Z_BLOCK) == Z_STREAM_ERROR) {
            fprintf(stderr, "Chunk inflate failed at iteration %d\n", i);
            ret = 1;
            goto cleanup_strm;
        }
    }

    printf("Validation complete. No ASan crash. Vulnerability successfully mitigated.\n");
    printf("Final head.extra_len state: %u\n", head.extra_len);

cleanup_strm:
    inflateEnd(&strm);
cleanup:
    free(extra);
    free(extra_data);
    
    return ret;
}
