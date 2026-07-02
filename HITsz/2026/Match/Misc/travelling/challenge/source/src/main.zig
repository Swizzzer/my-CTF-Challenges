const std = @import("std");
const http = @import("challenge");

pub fn main(init: std.process.Init) !void {
    var args = try std.process.Args.Iterator.initAllocator(init.minimal.args, init.gpa);
    defer args.deinit();

    _ = args.next();
    const port = args.next() orelse "8000";

    try http.serveForever(init.io, port);
}
