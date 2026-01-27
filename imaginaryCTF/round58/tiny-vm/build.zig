const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{ .default_target = .{ .cpu_arch = .x86_64, .os_tag = .linux } });
    const optimize = b.standardOptimizeOption(.{});
    const mod = b.addModule("tiny_vm", .{
        .root_source_file = b.path("src/vm.zig"),
        .target = target,
    });

    const exe = b.addExecutable(.{
        .name = "tiny_vm",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "tiny_vm", .module = mod },
            },
        }),
    });
    b.installArtifact(exe);
}
