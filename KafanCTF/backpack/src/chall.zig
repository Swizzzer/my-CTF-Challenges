const std = @import("std");
const print = std.debug.print;

const FLAG_LENGTH = 28;

fn enc(flag: []const u8, a: []const u64, ct: []u64) void {
    var bitstrings: [FLAG_LENGTH - 1][17]u8 = undefined;

    for (0..FLAG_LENGTH - 1) |i| {
        @memset(&bitstrings[i], 0);
    }

    // 生成 bitstrings
    for (0..FLAG_LENGTH - 1) |i| {
        const chunk = [_]u8{ flag[i], flag[i + 1] };
        var sum_ord: u16 = @as(u16, chunk[0]) + @as(u16, chunk[1]);

        for (0..16) |j| {
            bitstrings[i][15 - j] = if (sum_ord % 2 == 1) '1' else '0';
            sum_ord /= 2;
        }
    }

    for (0..FLAG_LENGTH - 1) |i| {
        var curr: u64 = 0;
        for (0..16) |j| {
            if (bitstrings[i][j] == '1') {
                const prev = curr;
                curr += a[j];
                // 检查溢出
                if (curr < prev) {
                    print("Integer overflow detected\n", .{});
                    std.process.exit(1);
                }
            }
        }
        ct[i] = curr;
    }
}

pub fn main() !void {
    const a = [_]u64{ 391141429, 3478124220, 3336047727, 3527421942, 1597786510, 2019990264, 2744862007, 3898825252, 486177504, 184886860, 781690097, 63429722, 1180618910, 1947105626, 1555881410, 2578824499 };

    const mt = [_]u64{ 2290375496, 6377613399, 1851683274, 3008635871, 4955741497, 4493937495, 7933494809, 3313318585, 5587460370, 2681599712, 2618169990, 5354670310, 3407564684, 1851683274, 3862218622, 2290375496, 671064364, 671064364, 3249888863, 4805770273, 2618169990, 5354670310, 6049818905, 3313318585, 2618169990, 5354670310, 2633373371 };

    const stdin = std.io.getStdIn().reader();
    var flag_buffer: [256]u8 = undefined;
    // flag = "flag{knapsack_is_a_backpack}"
    print("Enter flag: ", .{});

    if (try stdin.readUntilDelimiterOrEof(&flag_buffer, '\n')) |input| {
        // 如果有,则移除换行符
        const flag = std.mem.trimRight(u8, input, "\r\n");

        if (flag.len != FLAG_LENGTH) {
            print("Flag must be 28 characters long\n", .{});
            return;
        }

        var ct = [_]u64{0} ** (FLAG_LENGTH - 1);

        enc(flag, &a, &ct);

        var match = true;
        for (0..FLAG_LENGTH - 1) |i| {
            if (ct[i] != mt[i]) {
                match = false;
                break;
            }
        }

        if (match) {
            print("Congratulations! You got the correct flag~\n", .{});
        } else {
            print("Try again!\n", .{});
        }
    } else {
        print("Invalid input\n", .{});
    }
}
