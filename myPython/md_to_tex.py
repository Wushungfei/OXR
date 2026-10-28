#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown → LaTeX(.tex) 工程转换脚本
====================================
解决 OXR 输出的 md 文件图片是远程 URL（会过期丢失）的问题：

  1. 扫描 md 文件里所有 ![](http...) 远程图片
  2. 下载到本地 images/ 目录，并把引用改写为相对路径
  3. 用 pandoc 把"本地化后的 md"转换为 .tex 工程（含 xeCJK 中文支持）
  4. 生成同名编译说明书 README.txt（如何编译成 PDF）

用法:
    python md_to_tex.py 某文件.md
    python md_to_tex.py D:\\转换结果目录           (处理目录下所有 .md)
    python md_to_tex.py 某文件.md --out D:\\tex工程目录

输出目录结构（默认与 md 同目录）:
    <文档名>/
        document.tex      主 LaTeX 文件
        images/           本地化后的图片
        README.txt        编译说明

依赖: pip install pypandoc_binary -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
"""

import argparse
import re
import sys
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    import pypandoc
except ImportError:
    print("[错误] 未安装 pypandoc，请先执行:")
    print("    python -m pip install pypandoc_binary -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com")
    sys.exit(2)

# ------------------------- 配置 -------------------------
DOWNLOAD_TIMEOUT = 60       # 单张图片下载超时（秒）
DOWNLOAD_RETRIES = 3        # 单张图片重试次数
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"  # 下载图片用的 UA
# LaTeX 导言区：xeCJK 中文支持 + 常用字体（Windows 自带宋体/黑体）
LATEX_HEADER = r"""
\\usepackage{xeCJK}
\\setCJKmainfont{SimSun}
\\setCJKsansfont{Microsoft YaHei}
\\setCJKmonofont{FangSong}
\\usepackage{graphicx}
\\usepackage{longtable}
\\usepackage{booktabs}
"""
# --------------------------------------------------------

# 匹配 markdown 图片引用: ![alt](url) 或 ![](url)
IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

# 让 Windows 老终端正常打印中文
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def download_image(url: str, dest: Path) -> bool:
    """下载单张图片（跟随重定向），失败返回 False。"""
    for attempt in range(DOWNLOAD_RETRIES):
        try:
            req = Request(url, headers={"User-Agent": UA})
            with urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            return dest.stat().st_size > 0
        except Exception:
            if attempt < DOWNLOAD_RETRIES - 1:
                time.sleep(3 * (attempt + 1))
    return False


def guess_ext(url: str, default: str = ".png") -> str:
    """从 URL 猜测图片扩展名。"""
    path = urlparse(url).path.lower()
    for ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return default


def localize_images(md_text: str, img_dir: Path, doc_prefix: str) -> tuple[str, int, int]:
    """把 md 中所有远程图片下载到 img_dir 并改写为相对路径。返回(新md, 成功数, 失败数)。"""
    img_dir.mkdir(parents=True, exist_ok=True)
    urls = [m.group(2) for m in IMG_PATTERN.finditer(md_text) if m.group(2).startswith("http")]
    url_map = {}
    ok = fail = 0
    for i, url in enumerate(urls, 1):
        if url in url_map:
            continue
        # 用 URL 哈希前 8 位命名，避免重名且同一图不重复下载
        stem = hashlib.md5(url.encode()).hexdigest()[:8]
        fname = f"{doc_prefix}_fig{i:02d}_{stem}{guess_ext(url)}"
        dest = img_dir / fname
        print(f"    图片 {i}/{len(urls)}: {url.split('/')[-1][:40]}...", end=" ")
        if dest.exists() and dest.stat().st_size > 0:
            print("已存在, 跳过")
            url_map[url] = fname
            ok += 1
            continue
        if download_image(url, dest):
            print(f"OK ({dest.stat().st_size/1024:.0f} KB)")
            url_map[url] = fname
            ok += 1
        else:
            print("失败!")
            fail += 1
    # 改写 md 引用（失败的保留原 URL 并标注）
    def _replace(m):
        alt, url = m.group(1), m.group(2)
        if url in url_map:
            return f"![{alt}](images/{url_map[url]})"
        return m.group(0)
    return IMG_PATTERN.sub(_replace, md_text), ok, fail


def md_to_tex(md_path: Path, out_dir: Path) -> Path:
    """把单个 md 文件转换为 LaTeX 工程。返回 .tex 路径。"""
    project = out_dir / md_path.stem
    project.mkdir(parents=True, exist_ok=True)
    img_dir = project / "images"

    print(f"[处理] {md_path}")
    md_text = md_path.read_text(encoding="utf-8")

    if "![](http" in md_text or re.search(r"!\[[^\]]*\]\(http", md_text):
        new_md, ok, fail = localize_images(md_text, img_dir, md_path.stem)
        if fail:
            print(f"    [警告] {fail} 张图片下载失败（可能已过期），引用保留原 URL")
        md_text = new_md
    else:
        # 本地无远程图也建目录，保持工程结构一致
        img_dir.mkdir(parents=True, exist_ok=True)

    # 中间 md 存一份到工程里（resource-path 让 pandoc 能找到 images/）
    local_md = project / "source.md"
    local_md.write_text(md_text, encoding="utf-8")

    tex_path = project / "document.tex"
    pypandoc.convert_file(
        str(local_md),
        "latex",
        format="markdown+pipe_tables+tex_math_dollars+raw_tex",
        outputfile=str(tex_path),
        extra_args=[
            "--standalone",
            f"--resource-path={project}",
            f"--metadata=title={md_path.stem}",
            "-V", "geometry:a4paper",
            "-V", "fontsize=11pt",
            "--variable", f"header-includes:{LATEX_HEADER}",
        ],
    )
    print(f"    [完成] {tex_path} (+{len(list(img_dir.glob('*')))} 张图片)")
    return tex_path


def write_readme(project_dir: Path) -> None:
    """在工程里写编译说明。"""
    lines = [
        "=" * 50,
        "LaTeX 工程编译说明",
        "=" * 50,
        "",
        "生成的 document.tex 已包含 xeCJK 中文配置，",
        "图片已全部本地化到 images/ 目录。",
        "",
        "编译成 PDF 的两种方式:",
        "",
        "方式一: 在线编译（零安装）",
        "  访问 https://overleaf.com 新建项目,",
        "  把 document.tex 和 images/ 整个文件夹上传,",
        "  菜单 Menu -> Compiler 选择 XeLaTeX, 点 Recompile。",
        "",
        "方式二: 本机安装 TeX 发行版",
        "  1. 安装 TeX Live (https://tug.org/texlive) 或 MiKTeX (https://miktex.org)",
        "  2. 在本目录执行:",
        "     xelatex document.tex",
        "  3. 连续执行两次可生成正确目录/交叉引用",
        "",
        "字体说明: 使用 Windows 自带宋体(SimSun),",
        "若在 Linux/Overleaf 编译报字体错误, 把 document.tex 里的",
        "SimSun 改为 Noto Serif CJK SC 即可。",
    ]
    (project_dir / "README.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="md 转 LaTeX 工程（图片自动本地化）")
    parser.add_argument("path", help=".md 文件或包含 .md 的目录")
    parser.add_argument("--out", help="输出根目录（默认与 md 同目录）", default=None)
    args = parser.parse_args()

    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"[错误] 路径不存在: {target}")
        return 2

    mds = [target] if target.is_file() else sorted(target.glob("*.md"))
    if target.is_file() and target.suffix.lower() != ".md":
        print(f"[错误] 不是 .md 文件: {target}")
        return 2
    mds = [m for m in mds if m.suffix.lower() == ".md"]
    if not mds:
        print(f"[提示] 未找到 .md 文件: {target}")
        return 0

    out_root = Path(args.out).expanduser().resolve() if args.out else (target if target.is_dir() else target.parent)
    out_root.mkdir(parents=True, exist_ok=True)

    print(f"共 {len(mds)} 个 md 文件待转换  |  pandoc {pypandoc.get_pandoc_version()}")
    print("=" * 60)
    failed = []
    for md in mds:
        try:
            project = out_root / md.stem
            md_to_tex(md, out_root)
            write_readme(project)
        except KeyboardInterrupt:
            print("\n[中断] 已完成部分保留。")
            return 1
        except Exception as err:
            print(f"    [失败] {type(err).__name__}: {err}")
            failed.append(md.name)

    print("=" * 60)
    if failed:
        print(f"失败 {len(failed)} 个: {', '.join(failed)}")
        return 1
    print(f"全部完成。每个 md 对应一个同名文件夹（document.tex + images/ + README.txt）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
