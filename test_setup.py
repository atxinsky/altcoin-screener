#!/usr/bin/env python
"""
测试脚本 - 检查环境和依赖是否正确安装
"""
import sys

def test_python_version():
    """测试Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✓ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("  需要 Python 3.8+")
        return False

def test_imports():
    """测试依赖包导入"""
    print("\n检查依赖包...")
    packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'sqlalchemy': 'SQLAlchemy',
        'ccxt': 'CCXT',
        'pandas': 'Pandas',
        'pandas_ta': 'Pandas-TA',
        'plotly': 'Plotly',
        'pydantic': 'Pydantic',
    }

    success = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - 未安装")
            success = False

    return success

def test_config():
    """测试配置文件"""
    print("\n检查配置文件...")
    import os

    if os.path.exists('.env'):
        print("  ✓ .env 文件存在")

        # 读取配置检查是否填写API密钥
        with open('.env', 'r') as f:
            content = f.read()

        if 'your_binance_api_key_here' in content:
            print("  ⚠ 警告: 请填写币安API密钥")
            return False
        else:
            print("  ✓ API密钥已配置")
            return True
    else:
        print("  ✗ .env 文件不存在")
        print("  请复制 .env.example 为 .env 并填写配置")
        return False

def test_database():
    """测试数据库初始化"""
    print("\n测试数据库初始化...")
    try:
        from backend.database.database import init_db, engine
        init_db()
        print("  ✓ 数据库初始化成功")

        # 测试连接
        with engine.connect() as conn:
            print("  ✓ 数据库连接正常")
        return True
    except Exception as e:
        print(f"  ✗ 数据库初始化失败: {e}")
        return False

def test_binance_connection():
    """测试币安API连接"""
    print("\n测试币安API连接...")
    try:
        from backend.services.binance_service import BinanceService

        binance = BinanceService()
        overview = binance.get_market_overview()

        if overview.get('btc_price', 0) > 0:
            print(f"  ✓ 币安API连接成功")
            print(f"  BTC价格: ${overview['btc_price']:,.2f}")
            print(f"  ETH价格: ${overview['eth_price']:,.2f}")
            return True
        else:
            print("  ✗ 无法获取市场数据")
            return False

    except Exception as e:
        print(f"  ✗ 币安API连接失败: {e}")
        print("  请检查API密钥配置")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("币安山寨币筛选器 - 环境测试")
    print("=" * 60)

    results = []

    # 运行所有测试
    results.append(("Python版本", test_python_version()))
    results.append(("依赖包", test_imports()))
    results.append(("配置文件", test_config()))
    results.append(("数据库", test_database()))
    results.append(("币安API", test_binance_connection()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有测试通过！系统已就绪。")
        print("\n下一步:")
        print("  1. 运行 'python run_backend.py' 启动后端服务")
        print("  2. 运行 'python run_monitor.py' 启动监控服务")
        print("  3. 或运行 'start.bat' 使用图形化启动菜单")
    else:
        print("\n⚠️ 部分测试失败，请根据上述提示修复问题。")

if __name__ == "__main__":
    main()
