const std = @import("std");

pub fn main() !void {
    const input_path = "input.txt";
    const output_path = "output.txt";
    const input_file = try std.fs.cwd().openFile(input_path, .{ .mode = .read_only });
    defer input_file.close();
    const output_file = try std.fs.cwd().createFile(output_path, .{ .truncate = true });
    defer output_file.close();
    var buffered_reader = std.io.bufferedReader(input_file.reader());
    const reader = buffered_reader.reader();
    var buffered_writer = std.io.bufferedWriter(output_file.writer());
    const writer = buffered_writer.writer();
    const shuffle_order = @Vector(16, i32){ 7, -7, 1, 4, 3, -6, -4, 2, -2, 5, 6, 0, -1, -3, -5, -8 };
    var buffer: [16]u8 = undefined;
    while (true) {
        const bytes_read = try reader.readAll(&buffer);
        if (bytes_read == 0) break;

        if (bytes_read < 16) {
            @memset(buffer[bytes_read..], 0);
        }
        const vec1: @Vector(8, u8) = buffer[0..8].*;
        const vec2: @Vector(8, u8) = buffer[8..16].*;
        const shuffled_vec1 = @shuffle(u8, vec1, vec2, shuffle_order);

        try writer.writeAll(&@as([16]u8, shuffled_vec1));
    }
    try buffered_writer.flush();
    std.debug.print("Finished: {s} -> {s}\n", .{ input_path, output_path });
}
