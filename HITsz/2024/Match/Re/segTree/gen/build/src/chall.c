#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "flag.h"

void buildSegmentTree(int *segTree, int *arr, int start, int end, int node)
{
    if (start == end)
    {
        segTree[node] = arr[start];
    }
    else
    {
        int mid = (start + end) / 2;
        buildSegmentTree(segTree, arr, start, mid, 2 * node + 1);
        buildSegmentTree(segTree, arr, mid + 1, end, 2 * node + 2);
        segTree[node] = segTree[2 * node + 1] + segTree[2 * node + 2];
    }
}

int *createSegmentTree(const char *str, int n)
{
    int *arr = (int *)malloc(n * sizeof(int));
    for (int i = 0; i < n; i++)
    {
        arr[i] = (int)str[i];
    }

    int *segTree = (int *)malloc(4 * n * sizeof(int));
    buildSegmentTree(segTree, arr, 0, n - 1, 0);

    free(arr);
    return segTree;
}

int compareSegmentTrees(int *tree1, int *tree2, int n)
{
    for (int i = 0; i < 4 * n; i++)
    {
        if (tree1[i] != tree2[i])
        {
            return 0;
        }
    }
    return 1;
}

int main()
{

    char inputStr[100];
    printf("Enter a string: ");
    scanf("%s", inputStr);

    int n = sizeof(knownTree) / sizeof(knownTree[0]) / 4;

    int *inputTree = createSegmentTree(inputStr, n);

    if (compareSegmentTrees(knownTree, inputTree, n))
    {
        printf("Correct input!\n");
    }
    else
    {
        printf("Incorrect input.\n");
    }

    free(inputTree);
    return 0;
}
