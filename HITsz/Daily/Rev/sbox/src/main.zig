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

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const stdout = std.io.getStdOut().writer();
    const stdin = std.io.getStdIn().reader();

    try stdout.print("Gimme your flag\n", .{});
    try stdout.print("> ", .{});

    const input_buffer = try stdin.readUntilDelimiterAlloc(allocator, '\n', 1024);
    defer allocator.free(input_buffer);

    const input = std.mem.trimRight(u8, input_buffer, "\n");
    if (input.len != RES.len) {
        try stdout.print("🚫\n", .{});
        return;
    }

    var sboxed = try allocator.alloc(u8, input.len);
    defer allocator.free(sboxed);

    for (input, 0..) |c, i| {
        sboxed[i] = S_BOX[c];
    }

    for (sboxed, 0..) |*byte, i| {
        byte.* ^= KEY[i % KEY.len];
    }
    if (std.mem.eql(u8, sboxed, RES)) {
        try stdout.print("✅\n", .{});
    } else {
        try stdout.print("🚫\n", .{});
    }
}
