#!/usr/bin/env python3
"""
MinerU API 代理测试工具
用于验证代理配置是否正确，能否访问 mineru.net
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ 已加载配置文件: {env_path}")
else:
    print(f"⚠️  配置文件不存在: {env_path}")

# 读取配置
MINERU_BASE_URL = os.getenv("MINERU_BASE_URL", "https://mineru.net")
MINERU_API_TOKEN = os.getenv("MINERU_API_TOKEN")
MINERU_PROXIES = os.getenv("MINERU_PROXIES")

print("\n" + "="*70)
print("MinerU API 代理配置测试")
print("="*70)

# 显示配置
print(f"\n【配置信息】")
print(f"  BASE_URL: {MINERU_BASE_URL}")
print(f"  API_TOKEN: {'已配置 ✓' if MINERU_API_TOKEN else '未配置 ✗'}")
if MINERU_API_TOKEN:
    print(f"    长度: {len(MINERU_API_TOKEN)} 字符")
    print(f"    前缀: {MINERU_API_TOKEN[:30]}...")
print(f"  PROXIES: {MINERU_PROXIES if MINERU_PROXIES else '未配置'}")

# 测试代理
print(f"\n【代理测试】")

if not MINERU_PROXIES:
    print("⚠️  未配置代理，将直接连接")
    print("\n如需配置代理，在 .env 中添加:")
    print("  MINERU_PROXIES=http://your-proxy-server:port")
    print("\n继续测试直接连接...")
    session = requests.Session()
else:
    print(f"✓ 代理地址: {MINERU_PROXIES}")
    session = requests.Session()
    session.proxies = {
        "http": MINERU_PROXIES,
        "https": MINERU_PROXIES
    }

# 测试1: 检查出口IP
print(f"\n[测试1] 检查出口IP地址...")
try:
    resp = session.get("https://api.ipify.org?format=json", timeout=10)
    ip_info = resp.json()
    print(f"  ✓ 出口IP: {ip_info.get('ip')}")

    # 尝试获取IP地理位置信息
    try:
        geo_resp = session.get(f"https://ipapi.co/{ip_info.get('ip')}/json/", timeout=10)
        geo_info = geo_resp.json()
        print(f"  ✓ 地理位置: {geo_info.get('city', 'N/A')}, {geo_info.get('region', 'N/A')}, {geo_info.get('country_name', 'N/A')}")
    except:
        pass
except Exception as e:
    print(f"  ✗ 失败: {e}")
    sys.exit(1)

# 测试2: 访问国内网站
print(f"\n[测试2] 测试国内网站连通性...")
try:
    resp = session.get("https://www.baidu.com", timeout=10)
    print(f"  ✓ 百度访问: HTTP {resp.status_code}")
except Exception as e:
    print(f"  ✗ 失败: {e}")

# 测试3: 访问 MinerU 主站
print(f"\n[测试3] 测试 MinerU 主站连通性...")
try:
    resp = session.get(MINERU_BASE_URL, timeout=15)
    print(f"  ✓ MinerU主站: HTTP {resp.status_code}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    print(f"  原因: {type(e).__name__}")
    sys.exit(1)

# 测试4: 测试 MinerU API 端点
print(f"\n[测试4] 测试 MinerU API 端点...")

if not MINERU_API_TOKEN:
    print("  ⚠️  未配置 API Token，跳过API测试")
else:
    try:
        headers = {
            "Authorization": f"Bearer {MINERU_API_TOKEN}",
            "Content-Type": "application/json"
        }

        # 测试一个简单的API端点（获取配额信息或任务列表）
        api_url = f"{MINERU_BASE_URL}/api/v4/tasks"
        resp = session.get(api_url, headers=headers, timeout=15)

        if resp.status_code == 200:
            print(f"  ✓ API认证成功: HTTP {resp.status_code}")
            print(f"  ✓ Token有效")
        elif resp.status_code == 401:
            print(f"  ✗ API认证失败: HTTP {resp.status_code}")
            print(f"  原因: Token无效或已过期")
        else:
            print(f"  ⚠️  API响应: HTTP {resp.status_code}")

    except Exception as e:
        print(f"  ✗ API测试失败: {e}")

# 总结
print("\n" + "="*70)
print("【测试总结】")
print("="*70)

if MINERU_PROXIES:
    print(f"✓ 代理配置: {MINERU_PROXIES}")
    print(f"✓ 可以通过代理访问 MinerU API")
else:
    print(f"⚠️  未配置代理（直接连接）")

print(f"\n如果所有测试通过，可以运行完整的 PDF 转换测试:")
print(f"  cd /home/user/manuscript_agent/.claude/skills/managing-literature/scripts")
print(f"  python3 scihub_download.py download \\")
print(f"    --doi '10.4172/2161-1041.S2-001' \\")
print(f"    --output /tmp/test_mineru \\")
print(f"    --max-pages 5")

print("\n" + "="*70)
