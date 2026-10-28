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
```

## 内置特性

| 特性 | 说明 |
|------|------|
| 断点续转 | 已有同名 .md/.json 的文件自动跳过，中断后重新运行即可接着转 |
| 自动重试 | 限流/超时/断线自动重试 3 次（15s/30s/60s 退避） |
| 失败汇总 | 结束时打印失败清单和原因，失败不影响其他文件 |
| 结果校验 | 转换后报告页数、耗时、输出文件大小 |

## 可调参数（脚本顶部 CONFIG 区）

- `BASE_URL`：默认免费 API（国外源），国内慢可改 `https://free-oxr.somark.cn/api/v1`
- `TIMEOUT_SECONDS`：单文件解析超时（默认 600s，长文档建议保持）
- `GAP_BETWEEN_FILES`：相邻文件间隔秒数（默认 2s，对免费 API 友好）

## 常见问题

- **提示未安装 somark**：`python -m pip install somark -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`
- **大量失败**：免费 API 有排队/限流，等几分钟后重新运行脚本（会自动续转）
- **哪个 python**：本机 somark 装在 WorkBuddy 内置 Python 里，若 cmd 中 `python` 不可用，直接双击 `run_convert.bat`
