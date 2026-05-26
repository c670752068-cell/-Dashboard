#!/bin/bash
# 双击此文件启动股票 Regime Dashboard
# 第一次运行会自动创建虚拟环境并安装依赖（大约 1-2 分钟）

# 出错时不要自动关窗，让用户看到原因
trap 'echo ""; echo "❌ 启动失败，请把上面的红字截图给 Claude 看。"; echo ""; read -p "按回车键关闭..." _' ERR

set -e

# 切到脚本所在目录
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "  📊 Regime Dashboard 启动器"
echo "============================================================"
echo ""

# 找一个可用的 python3
PY=""
for candidate in python3 /usr/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PY="$candidate"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "❌ 没找到 Python 3。"
    echo "   请先安装 Python 3.9 或更高版本：https://www.python.org/downloads/"
    echo ""
    read -p "按回车键关闭..." _
    exit 1
fi

echo "✅ 使用 Python: $($PY --version) ($PY)"
echo ""

# 第一次启动：创建 venv 并安装依赖
if [ ! -d "venv" ]; then
    echo "🔧 第一次启动，正在创建虚拟环境..."
    "$PY" -m venv venv
    # shellcheck disable=SC1091
    source venv/bin/activate
    echo "📦 正在安装依赖（streamlit / yfinance / pandas / numpy / matplotlib）..."
    echo "   这一步大约需要 1-2 分钟，请耐心等待..."
    pip install --quiet --upgrade pip
    pip install --quiet streamlit yfinance pandas numpy matplotlib
    echo "✅ 依赖安装完成。"
    echo ""
else
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

# 跳过 Streamlit 第一次启动时的邮箱询问
mkdir -p "$HOME/.streamlit"
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
    cat > "$HOME/.streamlit/credentials.toml" <<EOF
[general]
email = ""
EOF
fi

echo "🚀 启动 Dashboard..."
echo ""
echo "   浏览器会自动打开 http://localhost:8501"
echo "   想要关闭：按 Control+C 或者直接关掉这个终端窗口"
echo ""
echo "============================================================"
echo ""

# 启动 streamlit
streamlit run app.py --browser.gatherUsageStats false
