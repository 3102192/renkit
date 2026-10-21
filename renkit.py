#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""renkit v0.1 — 零依赖批量文件重命名器（跨平台，离线可用）

子命令：
  list     列出目录内文件（支持模式匹配），预览将匹配哪些
  preview  干跑：显示每个文件将变成什么名字，不实际改名
  rename   批量重命名（前缀/后缀/替换/序号四种规则）
  case     文件名大小写转换（lower/upper/capital）
  undo     撤销最近一次 rename（读取 renikt.undo.log）

规则说明（rename）：
  --prefix P      文件名前加前缀
  --suffix S      扩展名前加后缀
  --replace OLD=NEW   文件名片段替换（可多次）
  --index START   按序号重命名（保留扩展名），如 --index 1 -> 01.txt
  --pattern GLOB  只匹配指定模式，默认 *
  --dry           干跑，不实际改名（等同 preview）

用法：
  python3 renikt.py list 目录 --pattern "*.txt"
  python3 renikt.py preview 目录 --prefix "2026-"
  python3 renikt.py rename 目录 --replace "旧=新" --dry
  python3 renikt.py rename 目录 --index 1
  python3 renikt.py case 目录 --to lower
  python3 renikt.py undo 目录

依赖：Python 3.8+，无第三方包。所有操作先记录后执行，改名日志写 renikt.undo.log 供 undo。
"""

import os
import re
import sys
import glob as globmod


def log(*a):
    print(*a)


def list_files(directory, pattern="*"):
    """返回目录内匹配的文件绝对路径列表（排除目录本身与日志）。"""
    base = os.path.abspath(directory)
    if not os.path.isdir(base):
        log(f"错误：目录不存在 {base}")
        sys.exit(1)
    out = []
    for p in sorted(globmod.glob(os.path.join(base, pattern))):
        if os.path.isfile(p) and os.path.basename(p) != "renkit.undo.log":
            out.append(p)
    return out


def split_name(path):
    d = os.path.dirname(path)
    name = os.path.basename(path)
    if "." in name and not name.startswith("."):
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext
    else:
        stem, ext = name, ""
    return d, stem, ext


def apply_rules(stem, ext, prefix=None, suffix=None, replaces=None, index=None, index_start=1, index_width=2):
    new_stem = stem
    for old, new in (replaces or []):
        new_stem = new_stem.replace(old, new)
    if prefix:
        new_stem = prefix + new_stem
    if suffix:
        new_stem = new_stem + suffix
    if index is not None:
        new_stem = str(index).zfill(index_width)
    return new_stem, ext


def write_undo_log(directory, pairs):
    log_path = os.path.join(directory, "renkit.undo.log")
    with open(log_path, "a", encoding="utf-8") as f:
        for src, dst in pairs:
            f.write(f"{src}\t{dst}\n")


def read_undo_log(directory):
    log_path = os.path.join(directory, "renkit.undo.log")
    if not os.path.exists(log_path):
        return []
    out = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if "\t" in line:
                src, dst = line.split("\t", 1)
                out.append((src, dst))
    return out


def cmd_list(args):
    directory = args.pop(0) if args else "."
    pattern = args[1] if len(args) > 1 else "*"
    files = list_files(directory, pattern)
    for p in files:
        print(p)
    log(f"共 {len(files)} 个文件")


def cmd_preview(args):
    # preview 等价于 rename --dry：复用干跑逻辑
    cmd_rename(args + ["--dry"])


def cmd_rename(args):
    directory = args.pop(0) if args else "."
    pattern = "*"
    dry = False
    prefix = suffix = None
    replaces = []
    index = None
    index_start = 1
    index_width = 2
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--pattern":
            pattern = args[i + 1]; i += 2
        elif a == "--prefix":
            prefix = args[i + 1]; i += 2
        elif a == "--suffix":
            suffix = args[i + 1]; i += 2
        elif a == "--replace":
            ov = args[i + 1]
            if "=" in ov:
                replaces.append(tuple(ov.split("=", 1)))
            i += 2
        elif a == "--index":
            index = index_start; i += 2
        elif a == "--index-width":
            index_width = int(args[i + 1]); i += 2
        elif a == "--dry":
            dry = True; i += 1
        elif a.startswith("--"):
            log(f"未知参数 {a}"); sys.exit(1)
        else:
            break
    files = list_files(directory, pattern)
    if not files:
        log("无匹配文件")
        return
    pairs = []
    idx = index_start
    for p in files:
        d, stem, ext = split_name(p)
        ns, ne = apply_rules(stem, ext, prefix=prefix, suffix=suffix,
                             replaces=replaces, index=index, index_width=index_width)
        dst = os.path.join(d, ns + ne)
        if dst != p:
            pairs.append((p, dst))
        idx += 1
    if not pairs:
        log("没有需要改名的文件")
        return
    for src, dst in pairs:
        print(f"{os.path.basename(src)}  ->  {os.path.basename(dst)}")
    if dry:
        log(f"干跑完成，共 {len(pairs)} 个（未实际改名）")
        return
    # 冲突检测：目标名重复
    dst_names = [d for _, d in pairs]
    if len(dst_names) != len(set(dst_names)):
        log("错误：目标文件名存在冲突，中止（建议加 --index 或不同前缀）")
        sys.exit(1)
    write_undo_log(directory, pairs)
    for src, dst in pairs:
        if os.path.exists(dst):
            log(f"跳过：目标已存在 {os.path.basename(dst)}")
            continue
        os.rename(src, dst)
    log(f"已重命名 {len(pairs)} 个文件，日志写入 renikt.undo.log")


def cmd_case(args):
    directory = args.pop(0) if args else "."
    to = "lower"
    pattern = "*"
    dry = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--to":
            to = args[i + 1]; i += 2
        elif a == "--pattern":
            pattern = args[i + 1]; i += 2
        elif a == "--dry":
            dry = True; i += 1
        elif a.startswith("--"):
            log(f"未知参数 {a}"); sys.exit(1)
        else:
            break
    files = list_files(directory, pattern)
    pairs = []
    for p in files:
        d, stem, ext = split_name(p)
        ns = {"lower": stem.lower(), "upper": stem.upper(), "capital": stem.capitalize()}.get(to, stem)
        dst = os.path.join(d, ns + ext)
        if dst != p:
            pairs.append((p, dst))
    if not pairs:
        log("没有需要转换的文件")
        return
    for src, dst in pairs:
        print(f"{os.path.basename(src)}  ->  {os.path.basename(dst)}")
    if dry:
        log(f"干跑完成，共 {len(pairs)} 个（未实际改名）")
        return
    write_undo_log(directory, pairs)
    for src, dst in pairs:
        if os.path.exists(dst):
            log(f"跳过：目标已存在 {os.path.basename(dst)}")
            continue
        os.rename(src, dst)
    log(f"已转换 {len(pairs)} 个文件名")


def cmd_undo(args):
    directory = args.pop(0) if args else "."
    pairs = read_undo_log(directory)
    if not pairs:
        log("没有可撤销的记录")
        return
    done = 0
    for src, dst in pairs:
        if os.path.exists(dst):
            os.rename(dst, src)
            print(f"还原 {os.path.basename(dst)}  ->  {os.path.basename(src)}")
            done += 1
        elif os.path.exists(src):
            print(f"跳过：目标已不存在 {os.path.basename(dst)}")
        else:
            print(f"跳过：源和目标都不存在 {os.path.basename(dst)}")
    # 清空日志（本批已处理）
    with open(os.path.join(directory, "renkit.undo.log"), "w", encoding="utf-8") as f:
        pass
    log(f"已还原 {done} 个文件")


def main(argv):
    if not argv:
        log(__doc__)
        return 0
    cmd = argv[0]
    args = argv[1:]
    try:
        if cmd == "list":
            cmd_list(args)
        elif cmd == "preview":
            cmd_preview(args)
        elif cmd == "rename":
            cmd_rename(args)
        elif cmd == "case":
            cmd_case(args)
        elif cmd == "undo":
            cmd_undo(args)
        else:
            log(f"未知命令 {cmd}，可用：list / preview / rename / case / undo")
    except SystemExit:
        raise
    except Exception as e:
        log(f"执行出错：{e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
