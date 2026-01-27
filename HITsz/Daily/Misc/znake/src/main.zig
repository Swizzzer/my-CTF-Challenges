const std = @import("std");
const rl = @import("raylib");
const cipher = @import("cipher.zig");

const Vec2 = rl.Vector2;

const SCREEN_SIZE = 700;
const CELL_SIZE = 50;
const GRID_WIDTH = SCREEN_SIZE / CELL_SIZE;
const TICK_SPEED = 10;
const MAX_SNAKE_LEN = 256;
const POS_HEAD = 0;

const Direction = enum {
    UP,
    DOWN,
    LEFT,
    RIGHT,
};

const Snake = struct {
    const Self = @This();
    position: [MAX_SNAKE_LEN]Vec2,
    direction: Direction,
    length: u8,
    pub fn init(pl: *Self) void {
        pl.*.position = undefined;
        pl.*.direction = Direction.DOWN;
        pl.*.length = 3;
        for (0..pl.*.length) |i| {
            pl.*.position[i] = Vec2.init(0, 0);
        }
    }
    pub fn drawPlayer(pl: Self) void {
        for (0..pl.length) |i| {
            rl.drawRectangle(@intFromFloat(pl.position[i].x), @intFromFloat(pl.position[i].y), CELL_SIZE, CELL_SIZE, .green);
        }
    }
};

const Game = struct {
    const Self = @This();
    allocator: std.mem.Allocator,
    isRunning: bool,
    player: *Snake,
    item: Vec2,
    score: u32,
    moveAllowed: bool,
    prevPos: [MAX_SNAKE_LEN]Vec2,
    frameCounter: u64,
    flagRevealed: bool,
    flagText: ?[:0]const u8,

    pub fn init(game: *Self) void {
        game.*.isRunning = true;
        game.*.score = 0;
        game.*.moveAllowed = true;
        game.*.prevPos = undefined;
        game.*.frameCounter = 0;
        game.*.player.*.init();

        game.spawnFood();

        if (game.flagText) |text| {
            game.allocator.free(text);
        }
        game.*.flagRevealed = false;
        game.*.flagText = null;
    }

    pub fn drawFood(game: Self) void {
        rl.drawCircle(@intFromFloat(CELL_SIZE / 2 + game.item.x), @intFromFloat(CELL_SIZE / 2 + game.item.y), CELL_SIZE / 2, .red);
    }

    pub fn spawnFood(game: *Self) void {
        while (true) {
            const new_item_pos = Vec2.init(
                @floatFromInt(rl.getRandomValue(0, GRID_WIDTH - 1) * CELL_SIZE),
                @floatFromInt(rl.getRandomValue(0, GRID_WIDTH - 1) * CELL_SIZE),
            );

            var is_on_snake = false;
            // Check if the new position is on any part of the snake
            for (0..game.player.length) |i| {
                if (new_item_pos.x == game.player.position[i].x and new_item_pos.y == game.player.position[i].y) {
                    is_on_snake = true;
                    break;
                }
            }

            if (!is_on_snake) {
                game.item = new_item_pos;
                return;
            }
        }
    }

    pub fn tick(game: *Self) void {
        if (game.*.isRunning) {
            const pl = game.*.player;
            if (rl.isKeyPressed(.right) and game.*.moveAllowed and pl.*.direction != .LEFT) {
                pl.*.direction = Direction.RIGHT;
                game.*.moveAllowed = false;
            } else if (rl.isKeyPressed(.left) and game.*.moveAllowed and pl.*.direction != .RIGHT) {
                pl.*.direction = Direction.LEFT;
                game.*.moveAllowed = false;
            } else if (rl.isKeyPressed(.down) and game.*.moveAllowed and pl.*.direction != .UP) {
                pl.*.direction = Direction.DOWN;
                game.*.moveAllowed = false;
            } else if (rl.isKeyPressed(.up) and game.*.moveAllowed and pl.*.direction != .DOWN) {
                pl.*.direction = Direction.UP;
                game.*.moveAllowed = false;
            }
            for (0..pl.*.length) |i| {
                game.*.prevPos[i] = pl.*.position[i];
            }
            if (@mod(game.*.frameCounter, TICK_SPEED) == 0) {
                switch (pl.*.direction) {
                    .DOWN => pl.*.position[POS_HEAD].y += CELL_SIZE,
                    .UP => pl.*.position[POS_HEAD].y -= CELL_SIZE,
                    .LEFT => pl.*.position[POS_HEAD].x -= CELL_SIZE,
                    .RIGHT => pl.*.position[POS_HEAD].x += CELL_SIZE,
                }
                game.*.moveAllowed = true;
                for (1..pl.*.length) |i| {
                    pl.*.position[i] = game.*.prevPos[i - 1];
                }
            }
            if (pl.*.position[POS_HEAD].x == game.*.item.x and pl.*.position[POS_HEAD].y == game.*.item.y) {
                // IMPORTANT: Don't modify this!
                game.*.score += 10;
                pl.*.position[pl.*.length] = game.*.prevPos[pl.*.length - 1];
                pl.*.length += 1;

                game.spawnFood();

                if (game.*.score == 23 and !game.flagRevealed) {
                    game.*.flagRevealed = true;
                    reveal_flag: {
                        const plain_slice = cipher.getFlag(game.allocator) catch |err| {
                            std.debug.print("Failed to get flag: {any}\n", .{err});
                            break :reveal_flag;
                        };
                        defer game.allocator.free(plain_slice);
                        game.flagText = game.allocator.dupeZ(u8, plain_slice) catch |err| {
                            std.debug.print("Failed to allocate C-string: {any}\n", .{err});
                            break :reveal_flag;
                        };
                    }
                }
            }
            if (pl.*.position[POS_HEAD].x >= SCREEN_SIZE) {
                pl.*.position[POS_HEAD].x = 0;
            } else if (pl.*.position[POS_HEAD].x < 0) {
                pl.*.position[POS_HEAD].x = SCREEN_SIZE - CELL_SIZE;
            }
            if (pl.*.position[POS_HEAD].y >= SCREEN_SIZE) {
                pl.*.position[POS_HEAD].y = 0;
            } else if (pl.*.position[POS_HEAD].y < 0) {
                pl.*.position[POS_HEAD].y = SCREEN_SIZE - CELL_SIZE;
            }
            for (1..pl.*.length) |i| {
                if (pl.*.position[POS_HEAD].x == pl.*.position[i].x and pl.*.position[POS_HEAD].y == pl.*.position[i].y) {
                    game.*.isRunning = false;
                }
            }
            game.*.frameCounter += 1;
        } else {
            if (rl.isKeyPressed(.enter)) {
                game.*.init();
            }
        }
    }

    pub fn render(game: Self) void {
        rl.beginDrawing();
        defer rl.endDrawing();
        rl.clearBackground(.ray_white);
        if (game.isRunning) {
            var i: i32 = 0;
            while (i <= SCREEN_SIZE) {
                rl.drawLine(i, 0, i, SCREEN_SIZE, .dark_gray);
                rl.drawLine(0, i, SCREEN_SIZE, i, .dark_gray);
                i += CELL_SIZE;
            }
            game.drawFood();
            game.player.*.drawPlayer();
            rl.drawText(rl.textFormat("Score: %i", .{game.score}), 20, 20, 20, .black);
            if (game.flagText) |text| {
                const font_size = 30;
                const text_width = rl.measureText(text, font_size);
                rl.drawText(text, @divFloor(SCREEN_SIZE - text_width, 2), SCREEN_SIZE / 3, font_size, .blue);
            }
        } else {
            rl.drawText("Game over! Press ENTER to restart.", @divFloor(SCREEN_SIZE - rl.measureText("Game over! Press ENTER to restart.", 25), 2), SCREEN_SIZE / 2 - 35, 25, .black);
            rl.drawText(rl.textFormat("Your score: %i", .{game.score}), @divFloor(SCREEN_SIZE - rl.measureText(rl.textFormat("Your score: %i", .{game.score}), 25), 2), SCREEN_SIZE / 2, 25, .black);
        }
    }
};

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();
    rl.initWindow(SCREEN_SIZE, SCREEN_SIZE, "🐍🐍🐍");
    defer rl.closeWindow();
    var player = Snake{ .position = undefined, .direction = Direction.DOWN, .length = 3 };
    var game = Game{
        .allocator = allocator,
        .isRunning = false,
        .item = undefined,
        .score = 0,
        .player = &player,
        .moveAllowed = false,
        .prevPos = undefined,
        .frameCounter = 0,
        .flagRevealed = false,
        .flagText = null,
    };
    game.init();
    defer if (game.flagText) |text| allocator.free(text);
    rl.setTargetFPS(60);
    while (!rl.windowShouldClose()) {
        game.tick();
        game.render();
    }
}
