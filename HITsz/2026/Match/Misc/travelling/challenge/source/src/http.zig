const std = @import("std");

const net = std.Io.net;

const max_connections = 1000;
const buf_size = 65535;
const chunk_size = 1024;
const max_headers = 16;
const public_dir = "./public";
const index_html = "/index.html";
const not_found_html = "/404.html";
const response_protocol = "HTTP/1.1";

const Status = enum {
    ok,
    created,
    not_found,
    internal_server_error,

    fn code(status: Status) u16 {
        return switch (status) {
            .ok => 200,
            .created => 201,
            .not_found => 404,
            .internal_server_error => 500,
        };
    }

    fn reason(status: Status) []const u8 {
        return switch (status) {
            .ok => "OK",
            .created => "Created",
            .not_found => "Not found",
            .internal_server_error => "Internal Server Error",
        };
    }
};

pub const Header = struct {
    name: []const u8,
    value: []const u8,
};

const Request = struct {
    method: []const u8 = "",
    uri: []const u8 = "",
    qs: []const u8 = "",
    prot: []const u8 = "",
    payload: []const u8 = "",
    payload_size: usize = 0,
    headers: [max_headers]Header = undefined,
    header_count: usize = 0,

    fn header(self: *const Request, name: []const u8) ?[]const u8 {
        for (self.headers[0..self.header_count]) |h| {
            if (std.mem.eql(u8, h.name, name)) return h.value;
        }
        return null;
    }
};

const ParseError = error{BadRequest};

pub fn serveForever(io: std.Io, port_text: []const u8) !void {
    const port = try std.fmt.parseInt(u16, port_text, 10);
    var address = try net.IpAddress.parseIp4("0.0.0.0", port);
    var server = try address.listen(io, .{
        .kernel_backlog = max_connections,
        .reuse_address = true,
    });
    defer server.deinit(io);

    while (true) {
        const stream = server.accept(io) catch |err| {
            std.log.err("accept() error: {t}", .{err});
            return err;
        };

        handleClient(io, stream);
    }
}

fn handleClient(io: std.Io, accepted_stream: net.Stream) void {
    var stream = accepted_stream;
    defer stream.close(io);

    var input_buffer: [buf_size]u8 = undefined;
    var iovecs = [_][]u8{input_buffer[0..]};
    const read_len = io.vtable.netRead(io.userdata, stream.socket.handle, &iovecs) catch |err| {
        std.log.err("recv() error: {t}", .{err});
        return;
    };

    if (read_len == 0) {
        std.log.err("Client disconnected unexpectedly.", .{});
        return;
    }

    const request = parseRequest(input_buffer[0..read_len]) catch {
        writeErrorResponse(io, stream) catch {};
        return;
    };

    std.debug.print("\x1b[32m + [{s}] {s}\x1b[0m\n", .{ request.method, request.uri });
    for (request.headers[0..request.header_count]) |h| {
        std.debug.print("[H] {s}: {s}\n", .{ h.name, h.value });
    }

    var output_buffer: [4096]u8 = undefined;
    var stream_writer = stream.writer(io, &output_buffer);
    const writer = &stream_writer.interface;

    route(io, &request, writer) catch {};
    writer.flush() catch {};
    stream.shutdown(io, .send) catch {};
}

fn route(io: std.Io, request: *const Request, writer: *std.Io.Writer) !void {
    if (std.mem.eql(u8, request.method, "GET") and std.mem.eql(u8, request.uri, "/")) {
        var file_name: [20]u8 = undefined;
        const path = std.fmt.bufPrint(&file_name, "{s}{s}", .{ public_dir, index_html }) catch return writeStatus(writer, .internal_server_error);

        try writeStatus(writer, .ok);
        if (fileExists(io, path)) {
            writeFile(io, path, writer) catch {};
        } else {
            try writer.print("Hello! You are using {s}\n\n", .{request.header("User-Agent") orelse "(null)"});
        }
        return;
    }

    if (std.mem.eql(u8, request.method, "GET") and std.mem.eql(u8, request.uri, "/test")) {
        try writeStatus(writer, .ok);
        try writer.writeAll("List of request headers:\n\n");
        for (request.headers[0..request.header_count]) |h| {
            try writer.print("{s}: {s}\n", .{ h.name, h.value });
        }
        return;
    }

    if (std.mem.eql(u8, request.method, "POST") and std.mem.eql(u8, request.uri, "/")) {
        try writeStatus(writer, .created);
        try writer.print("Wow, seems that you POSTed {} bytes.\n", .{request.payload_size});
        try writer.writeAll("Fetch the data using `payload` variable.\n");
        if (request.payload_size > 0) {
            try writer.print("Request body: {s}", .{request.payload});
        }
        return;
    }

    if (std.mem.eql(u8, request.method, "GET")) {
        var file_name: [255]u8 = undefined;
        std.debug.print("0x{x}\n", .{@intFromPtr(&file_name)});

        const path = std.fmt.bufPrint(&file_name, "{s}{s}", .{ public_dir, request.uri }) catch {
            try writeStatus(writer, .not_found);
            try write404File(io, writer);
            return;
        };

        if (fileExists(io, path)) {
            try writeStatus(writer, .ok);
            writeFile(io, path, writer) catch {};
        } else {
            try writeStatus(writer, .not_found);
            try write404File(io, writer);
        }
        return;
    }

    try writeStatus(writer, .internal_server_error);
}

fn write404File(io: std.Io, writer: *std.Io.Writer) !void {
    var file_name: [20]u8 = undefined;
    const path = std.fmt.bufPrint(&file_name, "{s}{s}", .{ public_dir, not_found_html }) catch return;
    if (fileExists(io, path)) writeFile(io, path, writer) catch {};
}

fn writeStatus(writer: *std.Io.Writer, status: Status) !void {
    try writer.print("{s} {} {s}\n\n", .{ response_protocol, status.code(), status.reason() });
}

fn writeErrorResponse(io: std.Io, stream: net.Stream) !void {
    var output_buffer: [1024]u8 = undefined;
    var stream_writer = stream.writer(io, &output_buffer);
    const writer = &stream_writer.interface;
    try writeStatus(writer, .internal_server_error);
    try writer.flush();
}

fn fileExists(io: std.Io, file_name: []const u8) bool {
    std.Io.Dir.cwd().access(io, file_name, .{}) catch return false;
    return true;
}

fn writeFile(io: std.Io, file_name: []const u8, writer: *std.Io.Writer) !void {
    const file = try std.Io.Dir.cwd().openFile(io, file_name, .{});
    defer file.close(io);

    var buffer: [chunk_size]u8 = undefined;
    while (true) {
        const read_len = try std.posix.read(file.handle, &buffer);
        if (read_len == 0) break;
        try writer.writeAll(buffer[0..read_len]);
    }
}

fn parseRequest(buffer: []u8) ParseError!Request {
    const header_split = findHeaderEnd(buffer);
    const head = buffer[0..header_split.head_end];
    const body = buffer[header_split.body_start..];

    var lines = std.mem.splitScalar(u8, head, '\n');
    const request_line = trimLineEndMut(@constCast(lines.next() orelse return error.BadRequest));

    var index: usize = 0;
    const method = nextToken(request_line, &index, " \t\r\n") orelse return error.BadRequest;
    const uri_token = nextToken(request_line, &index, " \t\r\n") orelse return error.BadRequest;
    const prot = nextToken(request_line, &index, " \t\r\n") orelse return error.BadRequest;

    const uri_unescaped = uriUnescape(uri_token);

    var request: Request = .{
        .method = method,
        .uri = uri_unescaped,
        .qs = "",
        .prot = prot,
        .payload = body,
        .payload_size = body.len,
    };

    if (std.mem.indexOfScalar(u8, uri_unescaped, '?')) |query_index| {
        request.uri = uri_unescaped[0..query_index];
        request.qs = uri_unescaped[query_index + 1 ..];
    }

    while (lines.next()) |raw_line| {
        const line = trimLineEnd(raw_line);
        if (line.len == 0) break;
        if (request.header_count == max_headers) continue;

        const colon = std.mem.indexOfScalar(u8, line, ':') orelse continue;
        const name = std.mem.trim(u8, line[0..colon], " \t\r\n");
        const value = std.mem.trimStart(u8, line[colon + 1 ..], " \t");
        request.headers[request.header_count] = .{ .name = name, .value = value };
        request.header_count += 1;
    }

    if (request.header("Content-Length")) |value| {
        request.payload_size = std.fmt.parseInt(usize, value, 10) catch body.len;
    }

    return request;
}

const HeaderSplit = struct {
    head_end: usize,
    body_start: usize,
};

fn findHeaderEnd(buffer: []const u8) HeaderSplit {
    if (std.mem.indexOf(u8, buffer, "\r\n\r\n")) |index| {
        return .{ .head_end = index, .body_start = index + 4 };
    }
    if (std.mem.indexOf(u8, buffer, "\n\n")) |index| {
        return .{ .head_end = index, .body_start = index + 2 };
    }
    return .{ .head_end = buffer.len, .body_start = buffer.len };
}

fn trimLineEnd(line: []const u8) []const u8 {
    var end = line.len;
    while (end > 0 and line[end - 1] == '\r') end -= 1;
    return line[0..end];
}

fn trimLineEndMut(line: []u8) []u8 {
    var end = line.len;
    while (end > 0 and line[end - 1] == '\r') end -= 1;
    return line[0..end];
}

fn nextToken(line: []u8, index: *usize, delimiters: []const u8) ?[]u8 {
    while (index.* < line.len and contains(delimiters, line[index.*])) index.* += 1;
    if (index.* >= line.len) return null;

    const start = index.*;
    while (index.* < line.len and !contains(delimiters, line[index.*])) index.* += 1;
    return line[start..index.*];
}

fn contains(haystack: []const u8, needle: u8) bool {
    return std.mem.indexOfScalar(u8, haystack, needle) != null;
}

fn uriUnescape(uri: []u8) []u8 {
    var src: usize = 0;
    while (src < uri.len and !std.ascii.isWhitespace(uri[src]) and uri[src] != '%') {
        src += 1;
    }

    var dst = src;
    while (src < uri.len and !std.ascii.isWhitespace(uri[src])) {
        const chr = if (uri[src] == '+')
            ' '
        else if (uri[src] == '%' and src + 2 < uri.len) decoded: {
            src += 1;
            const high = cHexValue(uri[src]);
            src += 1;
            const low = cHexValue(uri[src]);
            break :decoded @as(u8, @truncate(high * 16 + low));
        } else
            uri[src];

        uri[dst] = chr;
        dst += 1;
        src += 1;
    }

    return uri[0..dst];
}

fn cHexValue(chr: u8) u16 {
    return @as(u16, chr & 0x0f) + 9 * @as(u16, @intFromBool(chr > '9'));
}

test "parse request line headers and body" {
    var request_bytes = "POST /?a=1 HTTP/1.1\r\nHost: example\r\nContent-Length: 5\r\n\r\nhello".*;
    const request = try parseRequest(&request_bytes);

    try std.testing.expectEqualStrings("POST", request.method);
    try std.testing.expectEqualStrings("/", request.uri);
    try std.testing.expectEqualStrings("a=1", request.qs);
    try std.testing.expectEqualStrings("HTTP/1.1", request.prot);
    try std.testing.expectEqualStrings("hello", request.payload);
    try std.testing.expectEqual(@as(usize, 5), request.payload_size);
    try std.testing.expectEqualStrings("example", request.header("Host").?);
}

test "uri unescape mirrors the C helper" {
    var encoded = "/a%20b+c".*;
    try std.testing.expectEqualStrings("/a b c", uriUnescape(&encoded));

    var plus_without_percent = "/a+b".*;
    try std.testing.expectEqualStrings("/a+b", uriUnescape(&plus_without_percent));
}
