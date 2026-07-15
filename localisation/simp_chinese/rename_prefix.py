#!/usr/bin/env python3
"""
文件名前缀替换脚本

功能：将当前目录及子目录中文件名带有指定前缀的文件，替换为新的前缀。
支持 dry-run 模式预览更改。

用法：
    python rename_prefix.py <旧前缀> <新前缀>
    python rename_prefix.py <旧前缀> <新前缀> --dry-run    # 仅预览，不实际重命名
    python rename_prefix.py <旧前缀> <新前缀> --dir         # 同时重命名目录
"""

import os
import argparse


def rename_items(root_dir, old_prefix, new_prefix, rename_dirs=False):
    """
    遍历目录，将文件名中的 old_prefix 替换为 new_prefix。

    参数：
        root_dir: 根目录路径
        old_prefix: 需要被替换的旧前缀
        new_prefix: 替换后的新前缀
        rename_dirs: 是否也重命名目录

    返回：
        (renamed_count, skipped_count): (重命名数量, 跳过数量)
    """
    renamed = 0
    skipped = 0
    results = []

    # 先收集所有需要重命名的条目，按深度排序（深的先处理，避免父目录重命名后子路径变化）
    # 如果重命名目录，先处理文件，后处理目录
    entries = []  # (original_path, new_name, is_dir, parent_dir)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 处理文件
        for name in filenames:
            if name.startswith(old_prefix):
                new_name = new_prefix + name[len(old_prefix):]
                entries.append((os.path.join(dirpath, name), new_name, False, dirpath))

        # 处理目录
        if rename_dirs:
            for name in dirnames:
                if name.startswith(old_prefix):
                    new_name = new_prefix + name[len(old_prefix):]
                    entries.append((os.path.join(dirpath, name), new_name, True, dirpath))

    # 如果重命名目录，按深度降序排列（子目录先处理）
    if rename_dirs:
        entries.sort(key=lambda x: x[0].count(os.sep), reverse=True)

    for original_path, new_name, is_dir, parent_dir in entries:
        new_path = os.path.join(parent_dir, new_name)

        if os.path.exists(new_path):
            results.append((original_path, new_path, False, is_dir, "目标文件已存在，跳过"))
            skipped += 1
            continue

        results.append((original_path, new_path, True, is_dir, ""))
        renamed += 1

    return results


def main():
    parser = argparse.ArgumentParser(
        description="将当前目录及子目录中文件名带有指定前缀的文件替换为新的前缀",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    python rename_prefix.py old_ new_        # 将 "old_xxx.txt" 重命名为 "new_xxx.txt"
    python rename_prefix.py img_ photo_      # 将 "img_001.png" 重命名为 "photo_001.png"
    python rename_prefix.py img_ photo_ --dry-run  # 预览更改
    python rename_prefix.py img_ photo_ --dir      # 同时重命名目录
        """,
    )
    parser.add_argument("old_prefix", help="需要被替换的旧前缀")
    parser.add_argument("new_prefix", help="替换后的新前缀")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览将要重命名的文件，不实际执行",
    )
    parser.add_argument(
        "--dir",
        action="store_true",
        dest="rename_dirs",
        help="同时重命名目录（默认只重命名文件）",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="指定根目录（默认为当前目录）",
    )

    args = parser.parse_args()

    root_dir = os.path.abspath(args.root)
    print(f"扫描目录: {root_dir}")
    print(f"旧前缀: '{args.old_prefix}'  ->  新前缀: '{args.new_prefix}'")
    print(f"重命名目录: {'是' if args.rename_dirs else '否'}")
    print("-" * 60)

    results = rename_items(root_dir, args.old_prefix, args.new_prefix, args.rename_dirs)

    if not results:
        print("没有找到需要重命名的文件。")
        return

    # 分别统计成功和跳过的
    success_results = [r for r in results if r[2]]
    skipped_results = [r for r in results if not r[2]]

    for original, new_path, will_rename, is_dir, reason in results:
        item_type = "[目录]" if is_dir else "[文件]"
        if will_rename:
            action = "[将重命名]" if args.dry_run else "[已重命名]"
            print(f"  {action} {item_type} {os.path.basename(original)}")
            print(f"          -> {os.path.basename(new_path)}")
        else:
            print(f"  [跳过]  {item_type} {os.path.basename(original)} - {reason}")

    print("-" * 60)
    print(f"总计: {len(results)} 个匹配项")
    print(f"  - 将重命名: {len(success_results)} 个")
    print(f"  - 跳过:     {len(skipped_results)} 个")

    # 执行重命名（非 dry-run 模式）
    if not args.dry_run:
        confirm = input(f"\n确认执行以上 {len(success_results)} 个重命名操作？(y/N): ")
        if confirm.lower() not in ("y", "yes"):
            print("已取消操作。")
            return

        renamed_count = 0
        failed_count = 0
        for original, new_path, will_rename, is_dir, _ in results:
            if not will_rename:
                continue
            try:
                os.rename(original, new_path)
                renamed_count += 1
                item_type = "目录" if is_dir else "文件"
                print(f"  ✓ {item_type}: {os.path.basename(original)} -> {os.path.basename(new_path)}")
            except OSError as e:
                failed_count += 1
                print(f"  ✗ 重命名失败: {original} -> {e}")

        print(f"\n完成！成功: {renamed_count}, 失败: {failed_count}")
    else:
        print(f"\n这是预览结果，使用 --dry-run 仅查看不执行。去掉 --dry-run 即可实际重命名。")


if __name__ == "__main__":
    main()
