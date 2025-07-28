#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void buildSegmentTree(int* segTree, int* arr, int start, int end, int node) {
    if (start == end) {
        segTree[node] = arr[start];
    } else {
        int mid = (start + end) / 2;
        buildSegmentTree(segTree, arr, start, mid, 2 * node + 1);
        buildSegmentTree(segTree, arr, mid + 1, end, 2 * node + 2);
        segTree[node] = segTree[2 * node + 1] + segTree[2 * node + 2];
    }
}

int* createSegmentTree(const char* str, int n) {
    int* arr = (int*)malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) {
        arr[i] = (int)str[i];
    }

    int* segTree = (int*)malloc(4 * n * sizeof(int));
    buildSegmentTree(segTree, arr, 0, n - 1, 0);

    free(arr);
    return segTree;
}

int main() {
    char knownStr[] = "FLAG_TEMPLATE";  // Dynamic flag
    int n = strlen(knownStr);

    int* knownTree = createSegmentTree(knownStr, n);
    
    // Print the segment tree
    printf("int knownTree[] = {");
    for (int i = 0; i < 4 * n; i++) {
        printf("%d", knownTree[i]);
        if (i < 4 * n - 1) {
            printf(", ");
        }
    }
    printf("};\n");

    free(knownTree);
    return 0;
}
