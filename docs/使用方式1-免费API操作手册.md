# OXR 第一种使用方式：somark CLI + 免费 API（操作手册）

> 适用场景：不需要本地部署，直接用 SoMark 官方免费 API 解析文档。
> 本机已验证跑通（2026-10-28），Python 3.13 + somark 0.1.0。

## 一、前置条件（本机已就绪）

| 项目 | 状态 |
|------|------|
| Python ≥ 3.10 | ✅ 本机为 3.13（WorkBuddy 内置版） |
| somark 包 | ✅ 已安装，命令位置：`C:\Users\Admin\.workbuddy\binaries\python\versions\3.13.12\Scripts\somark.exe` |
| PATH | ✅ 已将该目录加入用户 PATH（新开的 cmd 窗口生效） |

注意：你这台机器上只有 WorkBuddy 内置的 Python，没有单独安装系统级 Python。
如果你在自己的 cmd 里敲 `python` 没反应，说明用的就是这个内置版，路径如上。

## 二、详细操作步骤

### 第 1 步：打开命令行

按 `Win + R`，输入 `cmd` 回车。
（如果新窗口里 `somark --version` 提示找不到命令，先关掉重开一个 cmd——
PATH 是刚才才加的，旧窗口不认识。）

### 第 2 步：确认命令可用

```cmd
somark --version
```

能打印版本号即 OK。

### 第 3 步：解析文档（核心命令）

把下面命令里的 `你的文件.pdf` 换成实际文件名，在 cmd 里执行：

```cmd
somark --base-url https://free-oxr.somark.ai/api/v1 --api-key dummy parse 你的文件.pdf --formats md,json --out 输出目录\
```

⚠️ 两个本机实测的坑：
1. **输出目录必须先创建**，否则报错 `output directory does not exist`。先 `mkdir 输出目录`。
2. API Key 填 `dummy` 即可（免费 API 不需要真实 key，但参数不能省）。

完整示例（先建目录再解析）：

```cmd
mkdir C:\Users\Admin\oxr-out
somark --base-url https://free-oxr.somark.ai/api/v1 --api-key dummy parse C:\Users\Admin\test_doc.png --formats md --out C:\Users\Admin\oxr-out\
```

### 第 4 步：查看结果

解析完成后，输出目录里会出现同名 `.md` / `.json` 文件，用任意编辑器打开即可。

本机实测结果（test_doc.png → test_doc.md）：文字内容全部正确识别。

## 三、常用参数速查（somark parse）

| 参数 | 作用 |
|------|------|
| `--formats md,json` | 输出格式：markdown / json |
| `--out 目录\` | 输出目录（必须预先存在） |
| `--table-fmt html` | 表格输出为 HTML（默认 markdown） |
| `--formula-fmt latex` | 公式输出 LaTeX（默认） |
| `--keep-header-footer` | 保留页眉页脚（默认过滤掉） |
| `--image-fmt base64` | 图片内嵌为 base64（默认 url） |
| `--async` + `--task-id xxx --wait` | 异步解析大文件 |
| 多文件：`parse a.pdf b.pdf` | 一次解析多个文件 |
| `--file-list 清单.txt` | 批量解析（一行一个文件路径） |

## 四、备选镜像（国内更快）

```cmd
somark --base-url https://free-oxr.somark.cn/api/v1 --api-key dummy parse 文件.pdf --formats md --out 目录\
```

（somark.cn 是 somark.ai 的国内镜像，功能相同。）

## 五、免费 API 限制

- 无需注册，但无稳定性保证，有排队机制，速率浮动
- 不建议用于生产环境（官方原话："直至我们的服务器顶不住压力"）
- 解析时会有 3 条无害警告（enable_image_understanding 等参数被忽略），不影响结果

## 六、如果想改用其他 Python

如果以后装了系统 Python（如从 python.org 下载），在那个 Python 里：

```cmd
python -m pip install somark -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

⚠️ 本机实测：PyPI 官方源和清华镜像走代理时极慢或失败，**阿里云镜像正常**，推荐加 `-i https://mirrors.aliyun.com/pypi/simple/`。
