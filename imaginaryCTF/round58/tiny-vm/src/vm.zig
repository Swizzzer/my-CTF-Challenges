const std = @import("std");

pub const key_bytes = "tinyVMkey!";
pub const flag_len: usize = 26;

pub const ExecError = error{
    StackOverflow,
    StackUnderflow,
    InvalidSIndex,
    InvalidInputIndex,
    InvalidOutputIndex,
};

pub const Reg = enum(u8) {
    J,
    Temp,
    I,
};

const REG_COUNT = 3;
const STACK_CAPACITY = 16;

pub const Instruction = union(enum) {
    push_imm: u16,
    load_reg: Reg,
    store_reg: Reg,
    add: void,
    xor: void,
    mod256: void,
    load_s: void,
    store_s: void,
    dup: void,
    pop: void,
    swap: void,
    load_input: void,
    store_output: void,
};

pub const StackM = struct {
    stack: [STACK_CAPACITY]u16,
    sp: usize,
    regs: [REG_COUNT]u16,
    s: [256]u8,
    input: []const u8,
    output: []u8,

    pub fn init(input: []const u8, output: []u8) StackM {
        return .{
            .stack = undefined,
            .sp = 0,
            .regs = [_]u16{0} ** REG_COUNT,
            .s = blk: {
                var arr: [256]u8 = undefined;
                inline for (0..256) |i| {
                    arr[i] = @intCast(255 - i);
                }
                break :blk arr;
            },
            .input = input,
            .output = output,
        };
    }

    fn push(self: *StackM, value: u16) ExecError!void {
        if (self.sp >= STACK_CAPACITY) return ExecError.StackOverflow;
        self.stack[self.sp] = value;
        self.sp += 1;
    }

    fn pop(self: *StackM) ExecError!u16 {
        if (self.sp == 0) return ExecError.StackUnderflow;
        self.sp -= 1;
        return self.stack[self.sp];
    }

    fn peek(self: *StackM) ExecError!u16 {
        if (self.sp == 0) return ExecError.StackUnderflow;
        return self.stack[self.sp - 1];
    }

    fn swapTop(self: *StackM) ExecError!void {
        if (self.sp < 2) return ExecError.StackUnderflow;
        const top = self.stack[self.sp - 1];
        self.stack[self.sp - 1] = self.stack[self.sp - 2];
        self.stack[self.sp - 2] = top;
    }

    pub fn execute(self: *StackM, program: []const Instruction) ExecError!void {
        if (@inComptime()) {
            @setEvalBranchQuota(400000);
        }
        for (program) |inst| {
            switch (inst) {
                .push_imm => |value| try self.push(value),
                .load_reg => |reg| try self.push(self.regs[@intFromEnum(reg)]),
                .store_reg => |reg| {
                    const value = try self.pop();
                    self.regs[@intFromEnum(reg)] = value;
                },
                .add => {
                    const b = try self.pop();
                    const a = try self.pop();
                    try self.push(@intCast(a + b));
                },
                .xor => {
                    const b = try self.pop();
                    const a = try self.pop();
                    try self.push(@intCast(a ^ b));
                },
                .mod256 => {
                    const value = try self.pop();
                    try self.push(value % 256);
                },
                .load_s => {
                    const idx = try self.pop();
                    if (idx >= 256) return ExecError.InvalidSIndex;
                    try self.push(self.s[idx]);
                },
                .store_s => {
                    const value = try self.pop();
                    const idx = try self.pop();
                    if (idx >= 256) return ExecError.InvalidSIndex;
                    self.s[idx] = @intCast(value & 0xff);
                },
                .dup => {
                    const value = try self.peek();
                    try self.push(value);
                },
                .pop => {
                    _ = try self.pop();
                },
                .swap => try self.swapTop(),
                .load_input => {
                    const idx = try self.pop();
                    if (idx >= self.input.len) return ExecError.InvalidInputIndex;
                    try self.push(self.input[idx]);
                },
                .store_output => {
                    const value = try self.pop();
                    const idx = try self.pop();
                    if (idx >= self.output.len) return ExecError.InvalidOutputIndex;
                    self.output[idx] = @intCast(value & 0xff);
                },
            }
        }
    }
};

const shuffle_pairs = genShuffledPairs();

fn genExec(comptime msg_len: usize, comptime key: []const u8, emitter: anytype) void {
    @setEvalBranchQuota(400000);

    inline for (0..256) |i| {
        emitter.emit(.{ .push_imm = @intCast(i) });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .load_reg = .J });
        emitter.emit(.{ .add = {} });
        emitter.emit(.{ .push_imm = @intCast(key[i % key.len]) });
        emitter.emit(.{ .add = {} });
        emitter.emit(.{ .mod256 = {} });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .store_reg = .J });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .store_reg = .Temp });
        emitter.emit(.{ .load_reg = .J });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .swap = {} });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .store_s = {} });
        emitter.emit(.{ .load_reg = .J });
        emitter.emit(.{ .load_reg = .Temp });
        emitter.emit(.{ .store_s = {} });
    }

    emitter.emit(.{ .push_imm = @intCast(0) });
    emitter.emit(.{ .store_reg = .J });

    inline for (shuffle_pairs) |pair| {
        emitter.emit(.{ .push_imm = @intCast(pair[0]) });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .store_reg = .Temp });
        emitter.emit(.{ .push_imm = @intCast(pair[1]) });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .swap = {} });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .store_s = {} });
        emitter.emit(.{ .push_imm = @intCast(pair[1]) });
        emitter.emit(.{ .load_reg = .Temp });
        emitter.emit(.{ .store_s = {} });
    }

    emitter.emit(.{ .push_imm = @intCast(0) });
    emitter.emit(.{ .store_reg = .I });
    emitter.emit(.{ .push_imm = @intCast(0) });
    emitter.emit(.{ .store_reg = .J });

    inline for (0..msg_len) |n| {
        emitter.emit(.{ .load_reg = .I });
        emitter.emit(.{ .push_imm = @intCast(1) });
        emitter.emit(.{ .add = {} });
        emitter.emit(.{ .mod256 = {} });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .store_reg = .I });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .load_reg = .J });
        emitter.emit(.{ .add = {} });
        emitter.emit(.{ .mod256 = {} });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .store_reg = .J });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .store_reg = .Temp });
        emitter.emit(.{ .load_reg = .J });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .swap = {} });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .store_s = {} });
        emitter.emit(.{ .load_reg = .J });
        emitter.emit(.{ .load_reg = .Temp });
        emitter.emit(.{ .store_s = {} });
        emitter.emit(.{ .load_reg = .I });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .load_reg = .J });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .swap = {} });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .add = {} });
        emitter.emit(.{ .mod256 = {} });
        emitter.emit(.{ .swap = {} });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .dup = {} });
        emitter.emit(.{ .load_s = {} });
        emitter.emit(.{ .swap = {} });
        emitter.emit(.{ .pop = {} });
        emitter.emit(.{ .push_imm = @intCast(n) });
        emitter.emit(.{ .load_input = {} });
        emitter.emit(.{ .xor = {} });
        emitter.emit(.{ .push_imm = @intCast(n) });
        emitter.emit(.{ .swap = {} });
        emitter.emit(.{ .store_output = {} });
    }
}

fn compExecLen(comptime msg_len: usize, comptime key: []const u8) usize {
    var counter = struct {
        count: usize = 0,
        inline fn emit(self: *@This(), inst: Instruction) void {
            _ = inst;
            self.count += 1;
        }
    }{};
    genExec(msg_len, key, &counter);
    return counter.count;
}

fn buildExec(comptime msg_len: usize, comptime key: []const u8) [compExecLen(msg_len, key)]Instruction {
    const program_len = compExecLen(msg_len, key);
    var program: [program_len]Instruction = undefined;
    var writer = struct {
        program: *[program_len]Instruction,
        index: usize = 0,
        inline fn emit(self: *@This(), inst: Instruction) void {
            self.program[self.index] = inst;
            self.index += 1;
        }
    }{ .program = &program };
    genExec(msg_len, key, &writer);
    if (writer.index != program.len) {
        @compileError("program length mismatch");
    }
    return program;
}

fn genShuffledPairs() [255][2]u8 {
    var pairs: [255][2]u8 = undefined;
    var state: u32 = 0xDEADBEEF;
    var idx: usize = 0;
    var k: usize = 255;
    while (k > 0) : (k -= 1) {
        state = @truncate(@as(u64, state) * 1664525 + 1013904223);
        const rand_idx: u8 = @truncate(state % (k + 1));
        pairs[idx] = .{ @intCast(k), rand_idx };
        idx += 1;
    }
    return pairs;
}

pub const myProgram = buildExec(flag_len, key_bytes);

pub fn encRuntime(input: []const u8, output: []u8) (error{InvalidLength} || ExecError)!void {
    if (input.len != flag_len or output.len != flag_len) return error.InvalidLength;
    var machine = StackM.init(input, output);
    try machine.execute(myProgram[0..]);
}

fn encComptime(comptime input: []const u8) [input.len]u8 {
    if (input.len != flag_len) @compileError("compile-time input length mismatch");
    var out: [input.len]u8 = undefined;
    var machine = StackM.init(input, out[0..]);
    machine.execute(myProgram[0..]) catch {
        @compileError("VM execution failed at comptime");
    };
    return out;
}

pub const ct: [flag_len]u8 = encComptime("ictf{4_vm_4nd_Rc4_for_fuN}");

pub fn ifEqual(a: []const u8, b: []const u8) bool {
    if (a.len != b.len) return false;
    var diff: u8 = 0;
    for (a, b) |x, y| diff |= x ^ y;
    return diff == 0;
}
