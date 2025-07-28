import ast


def extract_leaves(seg_tree, node):
    if 2 * node + 1 >= len(seg_tree) or seg_tree[2 * node + 1] == 0:
        return [seg_tree[node]]
    else:
        left_leaves = extract_leaves(seg_tree, 2 * node + 1)
        right_leaves = extract_leaves(seg_tree, 2 * node + 2)
        return left_leaves + right_leaves


seg_tree = ast.literal_eval(open("output.txt").readline())
leaves = extract_leaves(seg_tree, 0)
flag = "".join([chr(x) for x in leaves])
print(flag)
