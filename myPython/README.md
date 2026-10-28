# OXR 批量转换脚本使用说明

## 快速开始

```cmd
:: 转换某个目录下所有 PDF（结果存回原目录）
python oxr_batch_convert.py D:\你的PDF目录

:: 指定输出目录
python oxr_batch_convert.py D:\你的PDF目录 --out D:\转换结果

:: 递归扫描子目录
python oxr_batch_convert.py D:\你的PDF目录 --recursive

:: 只输出 Markdown（不要 JSON）
python oxr_batch_convert.py D:\你的PDF目录 --formats md

:: 强制重转（忽略已有结果）
python oxr_batch_convert.py D:\你的PDF目录 --force

:: 转换单个文件
python oxr_batch_convert.py D:\某个文件.pdf --out D:\转换结果

:: PDF → MD → LaTeX 工程一条龙（图片自动下载到本地）
python oxr_batch_convert.py D:\你的PDF目录 --tex
```

## 生成 LaTeX 工程（--tex / md_to_tex.py）

OXR 输出的 md 里图片是**远程 URL**（服务器缓存约 1 小时后过期），直接转 PDF 必丢图。
`--tex` 会自动：下载全部远程图片到 `images/` → 改写为本地相对路径 → pandoc 生成 `document.tex`（含 xeCJK 中文配置）。

```
输出目录/tex_projects/<文档名>/
    document.tex    主 LaTeX 文件（可直接编译）
    images/         已本地化的图片
    source.md       本地化后的 md 源
    README.txt      编译说明
```

单独使用：`python md_to_tex.py 某文件.md --out 输出目录`

**编译成 PDF**：上传到 overleaf.com 选 XeLaTeX 编译（零安装），或本机装 TeX Live/MiKTeX 后执行 `xelatex document.tex`。

## 内置特性

| 特性 | 说明 |
|------|------|
| 断点续转 | 已有同名 .md/.json 的文件自动跳过，中断后重新运行即可接着转 |
| 自动重试 | 限流/超时/断线自动重试 3 次（15s/30s/60s 退避） |
| 失败汇总 | 结束时打印失败清单和原因，失败不影响其他文件 |
| 图片本地化 | --tex 模式下载全部远程图片（URL 哈希命名防重复，断点续传） |
| 结果校验 | 转换后报告页数、耗时、输出文件大小 |

## 可调参数（脚本顶部 CONFIG 区）

- `BASE_URL`：默认免费 API（国外源），国内慢可改 `https://free-oxr.somark.cn/api/v1`
- `TIMEOUT_SECONDS`：单文件解析超时（默认 600s，长文档建议保持）
- `GAP_BETWEEN_FILES`：相邻文件间隔秒数（默认 2s，对免费 API 友好）

## 常见问题

- **提示未安装 somark**：`python -m pip install somark -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`
- **大量失败**：免费 API 有排队/限流，等几分钟后重新运行脚本（会自动续转）
- **哪个 python**：本机 somark 装在 WorkBuddy 内置 Python 里，若 cmd 中 `python` 不可用，直接双击 `run_convert.bat`
