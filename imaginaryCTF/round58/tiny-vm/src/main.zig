const std = @import("std");
const challenge = @import("tiny_vm");

pub fn main() !void {
    var stdout_buffer: [1024]u8 = undefined;
    var stdout_writer = std.fs.File.stdout().writer(&stdout_buffer);
    const stdout = &stdout_writer.interface;
    var buffer: [challenge.flag_len + 2]u8 = undefined;
    var stdin_writer = std.fs.File.stdin().reader(&buffer);
    const stdin = &stdin_writer.interface;

    try stdout.print("🎫 Enter flag: ", .{});
    try stdout.flush();
    const raw = try stdin.takeDelimiterExclusive('\n');
    if (raw.len == 0) {
        try stdout.print("No input provided.\n", .{});
        try stdout.flush();
        return;
    }

    const input = std.mem.trimRight(u8, raw, "\r");

    if (input.len != challenge.flag_len) {
        try stdout.print("👿 Wrong length.\n", .{});
        try stdout.flush();
        return;
    }

    var cipher_buf: [challenge.flag_len]u8 = undefined;
    try challenge.encRuntime(input, cipher_buf[0..]);

    const success = challenge.ifEqual(cipher_buf[0..], challenge.ct[0..]);
    if (success) {
        try stdout.print("🎉 Correct!\n", .{});
        try stdout.flush();
    } else {
        try stdout.print("💪🏻 Try again~\n", .{});
        try stdout.flush();
    }
}
