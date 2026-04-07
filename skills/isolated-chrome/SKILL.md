---
name: isolated-chrome
description: 在独立的Chrome配置文件中打开新浏览器窗口，用于AI学习和执行自动化任务，不影响用户正在使用的浏览器。适用于：(1) 让AI学习网页内容而不干扰用户当前浏览 (2) 运行需要登录的自动化任务 (3) 并行执行多个独立的浏览器任务
---

# Isolated Chrome

用独立的Chrome profile打开新窗口，隔离操作不影响用户正在使用的浏览器。

## 使用场景

- 用户给链接让AI学习，但不想影响用户当前浏览的网页
- 需要登录账号进行自动化操作
- 同时运行多个独立的浏览器任务

## 核心方法

### 方法1：命令行直接打开（推荐）

```bash
# 使用随机profile目录，确保完全隔离
PROFILE_DIR=$(mktemp -d /tmp/isolated-chrome-XXXXX)
open -n -a "Google Chrome" --args --user-data-dir="$PROFILE_DIR"
```

### 方法2：AppleScript 控制

```bash
osascript -e 'tell application "Google Chrome" to make new window'
```

### 方法3：Python Selenium（需要自动化控制时）

```python
import os
import tempfile
from selenium import webdriver

profile_dir = tempfile.mkdtemp(prefix="isolated-chrome-")
options = webdriver.ChromeOptions()
options.add_argument(f"--user-data-dir={profile_dir}")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")

driver = webdriver.Chrome(options=options)
driver.get("https://example.com")
# ... 执行任务 ...
# driver.quit()  # 可选：保持浏览器打开
# import shutil; shutil.rmtree(profile_dir, ignore_errors=True)  # 清理
```

## 完整工作流示例

```bash
#!/bin/bash
# isolated_chrome.sh - 打开隔离Chrome并导航到URL

PROFILE_DIR=$(mktemp -d /tmp/isolated-chrome-XXXXX)
URL="${1:-https://www.google.com}"

echo "Opening isolated Chrome at: $PROFILE_DIR"
echo "Navigating to: $URL"

open -n -a "Google Chrome" --args \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    "$URL"

# 可选：记录profile路径供后续使用
echo "$PROFILE_DIR" > /tmp/last-isolated-chrome-profile
```

## 注意事项

- **每个profile目录 = 独立Chrome实例**：可同时运行多个，互不干扰
- **profile可复用**：重启后保留登录状态，适合需要登录的自动化任务
- **清理**：用完后可删除profile目录（`rm -rf /tmp/isolated-chrome-XXXXX`）
- **与用户Chrome隔离**：用户浏览的cookie、缓存、extensions完全不受影响

## 快速命令

```bash
# 打开新窗口（当前目录）
open -n -a "Google Chrome"

# 打开新窗口并导航到URL
open -n -a "Google Chrome" https://example.com

# 带隔离profile打开
open -n -a "Google Chrome" --args --user-data-dir=/tmp/my-isolated-profile
```
