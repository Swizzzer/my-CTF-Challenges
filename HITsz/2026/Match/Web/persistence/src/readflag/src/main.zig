const std = @import("std");
pub fn main() !void {
    try std.fs.File.stdout().writeAll("HITCTF{lOOks_l1ke_biG_file_upl0ad_buff3ring}\n");
}
