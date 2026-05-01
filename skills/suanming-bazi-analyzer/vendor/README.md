# vendor/

本目录存放第三方依赖的源码，直接内嵌到 skill 中，不依赖外部 pip install。

## lunar_python

- **来源**: https://github.com/6tail/lunar-python
- **版本**: 1.4.8
- **协议**: MIT
- **用途**: 农历/阳历转换、干支四柱、节气（精确到秒）、大运、纳音、神煞等底层计算

### 调用方式

skill 内所有脚本统一通过以下方式导入，不使用系统 pip 安装的版本：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vendor'))
from lunar_python import Solar, Lunar
```
