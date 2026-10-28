==================================================
LaTeX 工程编译说明
==================================================

生成的 document.tex 已包含 xeCJK 中文配置，
图片已全部本地化到 images/ 目录。

编译成 PDF 的两种方式:

方式一: 在线编译（零安装）
  访问 https://overleaf.com 新建项目,
  把 document.tex 和 images/ 整个文件夹上传,
  菜单 Menu -> Compiler 选择 XeLaTeX, 点 Recompile。

方式二: 本机安装 TeX 发行版
  1. 安装 TeX Live (https://tug.org/texlive) 或 MiKTeX (https://miktex.org)
  2. 在本目录执行:
     xelatex document.tex
  3. 连续执行两次可生成正确目录/交叉引用

字体说明: 使用 Windows 自带宋体(SimSun),
若在 Linux/Overleaf 编译报字体错误, 把 document.tex 里的
SimSun 改为 Noto Serif CJK SC 即可。