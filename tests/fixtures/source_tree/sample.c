#include <stdio.h>

void unrelated_function() {
    printf("Hello\n");
}

int vulnerable_function(int a,
                        int b) {
    int c = a + b;
    // Vulnerable line
    char buf[10];
    sprintf(buf, "%d", c);
    return c;
}
