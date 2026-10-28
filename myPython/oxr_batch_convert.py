#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OXR 批量文档转换脚本
====================
扫描指定路径下的所有 PDF 文件，通过 OXR 免费 API 批量转换为 Markdown / JSON。

用法示例:
    python oxr_batch_convert.py D:\\docs\\pdfs
    python oxr_batch_convert.py D:\\docs\\pdfs --formats md
    python oxr_batch_convert.py D:\\docs\\pdfs --recursive
    python oxr_batch_convert.py D:\\docs\\pdfs --out D:\\docs\\converted
    python oxr_batch_convert.py D:\\docs\\pdfs --force
    python oxr_batch_convert.py report.pdf

默认行为:
    - 转换结果 (.md/.json) 保存在 PDF 同目录下
    - 已有同名 .md 的文件自动跳过（断点续转），--force 可强制重转
    - 使用免费 API，无需真实 key

依赖: pip install somark -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
"""

import argparse
import sys
import time
import json
import warnings
from pathlib import Path

try:
    from somark import SoMark, SoMarkWarning
    from somark import (
        RateLimitError,
        TimeoutError,
        ConnectionError,
        ParseTimeoutError,
        ParseFailedError,
        APIError,
        SoMarkError,
    )
except ImportError:
    print("[错误] 未安装 somark 包，请先执行:")
    print("    python -m pip install somark -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com")
    sys.exit(2)

# ------------------------- 可按需修改的配置 -------------------------
# 免费 API 地址（国内慢可换成 https://free-oxr.somark.cn/api/v1）
BASE_URL = "https://free-oxr.somark.ai/api/v1"
API_KEY = "dummy"            # 免费 API 不校验，占位即可
TIMEOUT_SECONDS = 600        # 单个文件解析超时（长 PDF 建议保持较大值）
MAX_RETRIES = 3              # 单个文件失败重试次数
RETRY_WAIT = [15, 30, 60]    # 每次重试前等待秒数
GAP_BETWEEN_FILES = 2        # 相邻文件间隔（秒），对免费 API 友好一些
# --------------------------------------------------------------------

# 免费 API 每次都会返回的无害告警，直接屏蔽
warnings.simplefilter("ignore", SoMarkWarning)

# 让 Windows 老终端也能正常打印中文
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 可重试的临时性错误（限流/超时/断连）
TRANSIENT_ERRORS = (RateLimitError, TimeoutError, ConnectionError, ParseTimeoutError)


def collect_pdfs(target: Path, recursive: bool) -> list:
    """收集目标路径下所有 PDF 文件。"""
    if target.is_file():
        if target.suffix.lower() == ".pdf":
            return [target]
        print(f"[错误] 不是 PDF 文件: {target}")
        return []
    pattern = "**/*.pdf" if recursive else "*.pdf"
    pdfs = sorted(
        p for p in target.glob(pattern)
        if p.is_file() and p.suffix.lower() == ".pdf"
    )
    # glob 对大小写的兼容处理（Windows 下 *.pdf 已含 .PDF，这里再兜底一次）
    return pdfs


def output_paths(pdf: Path, out_dir: Path | None, formats: list) -> dict:
    """根据参数计算某个 PDF 对应的输出文件路径。"""
    base = out_dir if out_dir is not None else pdf.parent
    result = {}
    if "md" in formats:
        result["md"] = base / (pdf.stem + ".md")
    if "json" in formats:
        result["json"] = base / (pdf.stem + ".json")
    return result


def save_result(resp, paths: dict) -> None:
    """把解析结果写入文件。"""
    if "md" in paths:
        content = resp.md if resp.md is not None else ""
        paths["md"].write_text(content, encoding="utf-8")
    if "json" in paths:
        obj = resp.json_output if resp.json_output is not None else {}
        paths["json"].write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def parse_one(client: SoMark, pdf: Path) -> object:
    """解析单个文件，带重试与退避。"""
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return client.parser.parse(str(pdf), formats=["md", "json"])
        except TRANSIENT_ERRORS as err:
            last_error = err
            if attempt < MAX_RETRIES:
                wait = RETRY_WAIT[min(attempt, len(RETRY_WAIT) - 1)]
                print(f"    [重试] {type(err).__name__}: {err}，{wait}s 后第 {attempt + 1}/{MAX_RETRIES} 次重试...")
                time.sleep(wait)
        except (ParseFailedError, APIError, SoMarkError) as err:
            # 业务性失败，重试意义不大，直接放弃该文件
            raise
    raise last_error


def human_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}m{sec:02d}s"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="批量将 PDF 转换为 Markdown/JSON（基于 OXR 免费 API）"
    )
    parser.add_argument("path", help="PDF 文件或所在目录")
    parser.add_argument("--out", help="输出目录（默认与 PDF 同目录）", default=None)
    parser.add_argument(
        "--formats", help="输出格式，逗号分隔（默认 md,json）", default="md,json"
    )
    parser.add_argument("--recursive", "-r", help="递归扫描子目录", action="store_true")
    parser.add_argument("--force", help="忽略已有结果强制重转", action="store_true")
    parser.add_argument(
        "--tex", help="转换完成后自动生成 LaTeX 工程（图片本地化+.tex）", action="store_true"
    )
    args = parser.parse_args()

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    for f in formats:
        if f not in ("md", "json"):
            print(f"[错误] 不支持的格式: {f}（仅支持 md / json）")
            return 2

    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"[错误] 路径不存在: {target}")
        return 2

    out_dir = Path(args.out).expanduser().resolve() if args.out else None
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)

    pdfs = collect_pdfs(target, args.recursive)
    if not pdfs:
        print(f"[提示] 未找到 PDF 文件: {target}")
        return 0

    # 过滤已完成文件（断点续转）
    todo, skipped = [], []
    for pdf in pdfs:
        paths = output_paths(pdf, out_dir, formats)
        done = all(p.exists() and p.stat().st_size > 0 for p in paths.values())
        (todo if (args.force or not done) else skipped).append(pdf)

    print("=" * 62)
    print(f"OXR 批量转换  |  共 {len(pdfs)} 个 PDF")
    print(f"  待转换: {len(todo)}    已完成跳过: {len(skipped)}")
    print(f"  API: {BASE_URL}")
    print(f"  输出: {out_dir if out_dir else '与 PDF 同目录'}")
    print("=" * 62)

    if not todo:
        print("[完成] 所有文件均已转换过（如需重转加 --force）。")
        return 0

    succeeded, failed = [], []
    client = SoMark(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT_SECONDS)
    start_all = time.time()

    try:
        for idx, pdf in enumerate(todo, 1):
            paths = output_paths(pdf, out_dir, formats)
            print(f"[{idx}/{len(todo)}] {pdf.name}")
            t0 = time.time()
            try:
                resp = parse_one(client, pdf)
                save_result(resp, paths)
                elapsed = human_time(time.time() - t0)
                pages = getattr(resp, "pages", 0) or "?"
                size = sum(p.stat().st_size for p in paths.values())
                print(f"    [成功] {pages} 页, {elapsed}, 输出 "
                      f"{', '.join(p.name for p in paths.values())} ({size/1024:.1f} KB)")
                succeeded.append(pdf)
            except KeyboardInterrupt:
                print("\n[中断] 用户取消，已完成部分保留，下次运行自动续转。")
                break
            except Exception as err:
                elapsed = human_time(time.time() - t0)
                print(f"    [失败] {type(err).__name__}: {err} ({elapsed})")
                failed.append((pdf, f"{type(err).__name__}: {err}"))
            if idx < len(todo):
                time.sleep(GAP_BETWEEN_FILES)
    finally:
        client.close()

    total_time = human_time(time.time() - start_all)
    print("=" * 62)
    print(f"结束  |  成功 {len(succeeded)}  失败 {len(failed)}  跳过 {len(skipped)}  耗时 {total_time}")
    if failed:
        print("失败清单:")
        for pdf, reason in failed:
            print(f"  - {pdf.name}: {reason}")
        print("提示: 失败多为免费 API 限流/超时，直接重新运行本脚本即可续转（已成功的会自动跳过）。")
        return 1

    # --tex: 对成功结果生成 LaTeX 工程
    if args.tex and succeeded:
        print("=" * 62)
        print("[LaTeX] 开始生成 TeX 工程...")
        try:
            import subprocess
            script_dir = Path(__file__).parent / "md_to_tex.py"
            base = out_dir if out_dir is not None else target
            proc = subprocess.run(
                [sys.executable, str(script_dir), str(base), "--out", str(base / "tex_projects")],
                cwd=str(script_dir.parent),
            )
            if proc.returncode != 0:
                print("[LaTeX] 生成过程中有失败项，详见上方日志")
        except Exception as err:
            print(f"[LaTeX] 启动失败: {err}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
