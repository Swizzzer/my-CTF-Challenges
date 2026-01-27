# ======== Written by Swizzer & Copilot ========
import argparse
import os
from typing import List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import random
import csv

A = 1337137
B = 13371337


def first_x_from_seed(seed: int) -> int:
  rng = random.Random(seed)
  return rng.randint(A, B)


def f_from_x(x: int) -> int:
  rng = random.Random(x * x + x + 1)
  return rng.randint(A, B)


def detect_immediate_period(x1: int, max_period: int = 3) -> Tuple[int, List[int]]:
  for p in range(1, max_period + 1):
    x = x1
    for _ in range(p):
      x = f_from_x(x)
    if x == x1:
      # 恢复环序列
      cycle = [x1]
      cur = x1
      for _ in range(p - 1):
        cur = f_from_x(cur)
        cycle.append(cur)
      return p, cycle
  return 0, []


def floyd_cycle_length(x1: int, max_steps: int = 0) -> Tuple[int, int, List[int]]:
  """
  Floyd 算法：返回 (mu, lam, cycle_samples)
    - mu: 前导链长度
    - lam: 环长度
    - cycle_samples: 从环起点开始的环上序列（长度 lam）
  若 max_steps > 0 则作为安全上限（步数超过即放弃，返回 lam=0）。
  """
  # 第一阶段：寻找相遇点
  tort = f_from_x(x1)
  hare = f_from_x(f_from_x(x1))
  steps = 0
  while tort != hare:
    tort = f_from_x(tort)
    hare = f_from_x(f_from_x(hare))
    steps += 1
    if max_steps and steps > max_steps:
      return 0, 0, []

  # 第二阶段：求 mu（环起点）
  mu = 0
  tort = x1
  while tort != hare:
    tort = f_from_x(tort)
    hare = f_from_x(hare)
    mu += 1
    if max_steps and mu > max_steps:
      return 0, 0, []

  # 第三阶段：求 lam（环长度）
  lam = 1
  hare = f_from_x(tort)
  while tort != hare:
    hare = f_from_x(hare)
    lam += 1
    if max_steps and lam > max_steps:
      return 0, 0, []

  # 取环上的样本
  cycle = [tort]
  cur = tort
  for _ in range(lam - 1):
    cur = f_from_x(cur)
    cycle.append(cur)

  return mu, lam, cycle


def scan_seed_range(
  start: int, end: int, mode_eventual: bool, max_steps: int
) -> List[Tuple[int, int, int, List[int]]]:
  """
  扫描 [start, end]，返回命中周期<4的结果列表：
  (seed, mu, lam, cycle)
  """
  out: List[Tuple[int, int, int, List[int]]] = []
  for seed in range(start, end + 1):
    x1 = first_x_from_seed(seed)
    if mode_eventual:
      mu, lam, cycle = floyd_cycle_length(x1, max_steps=max_steps)
    else:
      p, cycle = detect_immediate_period(x1, max_period=3)
      mu, lam = (0, p) if p > 0 else (0, 0)

    if lam in (1, 2, 3):
      out.append((seed, mu, lam, cycle))
  return out


def chunk_ranges(start: int, end: int, chunk_size: int):
  s = start
  while s <= end:
    e = min(s + chunk_size - 1, end)
    yield (s, e)
    s = e + 1


def main():
  parser = argparse.ArgumentParser(
    description="多进程并行枚举，查找周期 < 4 的 PRNG seed"
  )
  parser.add_argument("--start", type=int, default=0, help="起始seed")
  parser.add_argument("--end", type=int, default=5000000, help="结束seed")
  parser.add_argument(
    "--eventual",
    action="store_true",
    help="使用 Floyd 算法检测最终进入的环；默认仅检测从首项开始的 1/2/3 环",
  )
  parser.add_argument(
    "--max-steps",
    type=int,
    default=0,
    help="Floyd 的安全步数上限（0 表示不限）。仅 --eventual 时有效。",
  )
  parser.add_argument(
    "--workers", type=int, default=os.cpu_count() or 4, help="进程数（默认=CPU核数）"
  )
  parser.add_argument(
    "--chunk-size", type=int, default=50_000, help="每个任务块的seed数量"
  )
  parser.add_argument(
    "--report",
    choices=["brief", "full"],
    default="brief",
    help="brief 仅输出seed与周期；full 额外输出环上的值",
  )
  parser.add_argument(
    "--out-csv", type=str, default="", help="将结果写入 CSV（列：seed,mu,period,cycle）"
  )
  args = parser.parse_args()

  tasks = list(chunk_ranges(args.start, args.end, args.chunk_size))
  total_seeds = args.end - args.start + 1
  done_seeds = 0
  results_all: List[Tuple[int, int, int, List[int]]] = []

  print(f"并行设置：workers={args.workers}, chunk_size={args.chunk_size}")
  print(
    f"搜索区间：[{args.start}, {args.end}]，模式：{'最终周期' if args.eventual else '即时周期'}"
  )
  print("开始扫描...")

  with ProcessPoolExecutor(max_workers=args.workers) as ex:
    fut2range = {
      ex.submit(scan_seed_range, s, e, args.eventual, args.max_steps): (s, e)
      for (s, e) in tasks
    }
    for fut in as_completed(fut2range):
      s, e = fut2range[fut]
      part = fut.result()
      results_all.extend(part)
      done_seeds += e - s + 1
      # 简单进度
      print(
        f"完成区间 [{s},{e}] -> 命中 {len(part)} 个；进度 {done_seeds}/{total_seeds} ({done_seeds * 100 / total_seeds:.2f}%)"
      )

  results_all.sort(key=lambda t: t[0])  # 按 seed 排序
  print(f"\n总命中种子数：{len(results_all)}\n")
  for seed, mu, lam, cycle in results_all:
    if args.report == "brief":
      print(f"seed={seed}  ->  period={lam}, mu={mu}")
    else:
      cyc_str = " -> ".join(str(v) for v in cycle) + (
        f" -> {cycle[0]}" if cycle else ""
      )
      print(f"seed={seed}  ->  period={lam}, mu={mu}, cycle: {cyc_str}")

  if args.out_csv:
    with open(args.out_csv, "w", newline="") as f:
      w = csv.writer(f)
      w.writerow(["seed", "mu", "period", "cycle"])
      for seed, mu, lam, cycle in results_all:
        w.writerow([seed, mu, lam, " ".join(map(str, cycle))])
    print(f"\n结果已写入：{args.out_csv}")


if __name__ == "__main__":
  main()
