#!/usr/bin/env python3
"""
邮件配置测试脚本
用于测试SMTP邮件发送是否正常工作
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from pathlib import Path

# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

def test_email_config():
    """测试邮件配置"""

    # 读取配置
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    email_to = os.getenv('EMAIL_TO', '')

    print("=" * 60)
    print("📧 邮件配置测试")
    print("=" * 60)
    print(f"\n配置信息：")
    print(f"  SMTP服务器: {smtp_host}")
    print(f"  SMTP端口: {smtp_port}")
    print(f"  发件人: {smtp_user}")
    print(f"  收件人: {email_to}")
    print(f"  密码: {'已配置 ✓' if smtp_password else '未配置 ✗'}")

    # 验证配置
    if not smtp_user or smtp_user == 'your_email@gmail.com':
        print("\n❌ 错误: 请先配置 SMTP_USER（发件人邮箱）")
        return False

    if not smtp_password or smtp_password == 'your_app_password':
        print("\n❌ 错误: 请先配置 SMTP_PASSWORD（应用专用密码）")
        print("\n💡 提示：")
        print("   1. Gmail需要生成应用专用密码（不是登录密码）")
        print("   2. 访问: https://myaccount.google.com/apppasswords")
        print("   3. 详细步骤请查看 邮箱设置指南.md")
        return False

    if not email_to or email_to == 'recipient@example.com':
        print("\n❌ 错误: 请先配置 EMAIL_TO（收件人邮箱）")
        return False

    # 创建测试邮件
    print("\n正在发送测试邮件...")

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email_to
        msg['Subject'] = f'🎉 币安筛选器 - 邮件配置测试成功 ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})'

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #26a69a;">✅ 邮件配置测试成功！</h2>

            <p>恭喜！您的邮件配置已正确设置。</p>

            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>配置信息：</h3>
                <ul>
                    <li><strong>SMTP服务器:</strong> {smtp_host}</li>
                    <li><strong>端口:</strong> {smtp_port}</li>
                    <li><strong>发件人:</strong> {smtp_user}</li>
                    <li><strong>收件人:</strong> {email_to}</li>
                    <li><strong>测试时间:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
                </ul>
            </div>

            <h3>接下来您将收到：</h3>
            <ul>
                <li>🔔 <strong>筛选结果通知</strong> - 发现高分机会时</li>
                <li>⚡ <strong>价格异动警报</strong> - 检测到显著价格变化时</li>
                <li>📊 <strong>定时监控报告</strong> - 市场概况和top机会</li>
            </ul>

            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 12px;">
                    此邮件由币安山寨币筛选器发送<br>
                    如需帮助，请查看 邮箱设置指南.md
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # 连接SMTP服务器
        print(f"  连接到 {smtp_host}:{smtp_port}...")

        if smtp_port == 465:
            # 使用SSL
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:
            # 使用STARTTLS
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.starttls()

        print("  正在登录...")
        server.login(smtp_user, smtp_password)

        print("  正在发送邮件...")
        server.send_message(msg)
        server.quit()

        print("\n" + "=" * 60)
        print("✅ 测试邮件发送成功！")
        print("=" * 60)
        print(f"\n请检查收件箱: {email_to}")
        print("（如果没有收到，请检查垃圾邮件文件夹）")
        print("\n配置正确，可以正常使用邮件通知功能！")

        return True

    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "=" * 60)
        print("❌ 认证失败")
        print("=" * 60)
        print("\n可能的原因：")
        print("  1. 应用专用密码错误")
        print("  2. Gmail需要启用两步验证并生成应用专用密码")
        print("  3. 用户名或密码包含特殊字符未正确转义")
        print(f"\n详细错误: {str(e)}")
        print("\n💡 解决方法：")
        print("  查看 邮箱设置指南.md 第1-2步")
        return False

    except smtplib.SMTPException as e:
        print("\n" + "=" * 60)
        print("❌ SMTP错误")
        print("=" * 60)
        print(f"\n错误信息: {str(e)}")
        print("\n可能的原因：")
        print("  1. SMTP服务器地址或端口错误")
        print("  2. 网络连接问题")
        print("  3. 防火墙阻止")
        return False

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 发送失败")
        print("=" * 60)
        print(f"\n错误信息: {str(e)}")
        print("\n💡 建议：")
        print("  1. 检查网络连接")
        print("  2. 确认.env文件中的配置正确")
        print("  3. 查看 邮箱设置指南.md")
        return False

if __name__ == "__main__":
    # 确保python-dotenv已安装
    try:
        import dotenv
    except ImportError:
        print("❌ 错误: 需要安装 python-dotenv")
        print("\n安装命令:")
        print("  pip install python-dotenv")
        exit(1)

    success = test_email_config()
    exit(0 if success else 1)
