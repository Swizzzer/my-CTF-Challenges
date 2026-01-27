const std = @import("std");

const S_BOX: [256]u8 = blk: {
    var sbox: [256]u8 = undefined;
    for (&sbox, 0..) |*byte, i| {
        byte.* = @intCast((i * 13 + 37) % 256);
    }
    break :blk sbox;
};

const KEY = "a_secret_xor_key";

// HITCTF{019381093810298310}
const RES: []const u8 = &.{
    172, 133, 26, 233, 10, 193, 1, 225, 253, 114, 211, 143, 253, 254, 111, 197, 156, 253, 230, 202, 105, 143, 217, 214, 202, 6,
};

const INV_S_BOX: [256]u8 = blk: {
    var inv_sbox: [256]u8 = undefined;

    for (S_BOX, 0..) |s_val, i| {
        inv_sbox[s_val] = @intCast(i);
    }
    break :blk inv_sbox;
};

// 因为本题考察的是CE的使用所以反逆向工作非常重要
// 以后只要修改cipher.zig就能方便地实现更复杂的加解密逻辑
// 另外记得在编译时使用Release选项以增大逆向难度
// 必要时还可以加Obfuscator
pub fn getFlag(allocator: std.mem.Allocator) ![]u8 {
    var plaintext = try allocator.alloc(u8, RES.len);

    for (RES, 0..) |cipher_byte, i| {
        const sboxed_char = cipher_byte ^ KEY[i % KEY.len];
        const plain_char = INV_S_BOX[sboxed_char];
        plaintext[i] = plain_char;
    }
    return plaintext;
}
