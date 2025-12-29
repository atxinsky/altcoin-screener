import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import asyncio
from typing import List, Optional
from telegram import Bot
from telegram.error import TelegramError
import os

from backend.config import settings
from backend.database.models import Alert
from sqlalchemy.orm import Session
from datetime import datetime


class NotificationService:
    """Service for sending email and Telegram notifications"""

    def __init__(self, db: Session):
        self.db = db
        self.telegram_bot = None

        if settings.TELEGRAM_BOT_TOKEN:
            try:
                self.telegram_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            except Exception as e:
                print(f"Failed to initialize Telegram bot: {e}")

    async def send_email(
        self,
        subject: str,
        body: str,
        html: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification

        Args:
            subject: Email subject
            body: Plain text body
            html: HTML body (optional)
            attachments: List of file paths to attach

        Returns:
            True if successful
        """
        if not all([settings.SMTP_USER, settings.SMTP_PASSWORD, settings.EMAIL_TO]):
            print("Email settings not configured")
            return False

        try:
            # 支持多个收件人（逗号分隔）
            recipients = [email.strip() for email in settings.EMAIL_TO.split(',')]

            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = settings.SMTP_USER
            message['To'] = ', '.join(recipients)  # 格式化为标准的收件人列表
            message['Subject'] = subject

            # Add text part
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)

            # Add HTML part if provided
            if html:
                html_part = MIMEText(html, 'html')
                message.attach(html_part)

            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            if filepath.endswith('.png') or filepath.endswith('.jpg'):
                                img = MIMEImage(f.read())
                                img.add_header('Content-Disposition', 'attachment',
                                             filename=os.path.basename(filepath))
                                message.attach(img)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )

            print(f"Email sent successfully: {subject}")
            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    async def send_telegram(
        self,
        message: str,
        image_path: Optional[str] = None
    ) -> bool:
        """
        Send Telegram notification

        Args:
            message: Message text
            image_path: Path to image to send (optional)

        Returns:
            True if successful
        """
        if not self.telegram_bot or not settings.TELEGRAM_CHAT_ID:
            print("Telegram settings not configured")
            return False

        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await self.telegram_bot.send_photo(
                        chat_id=settings.TELEGRAM_CHAT_ID,
                        photo=photo,
                        caption=message
                    )
            else:
                await self.telegram_bot.send_message(
                    chat_id=settings.TELEGRAM_CHAT_ID,
                    text=message,
                    parse_mode='HTML'
                )

            print("Telegram message sent successfully")
            return True

        except TelegramError as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    async def send_screening_alert(
        self,
        results: List[dict],
        timeframe: str,
        send_email: bool = True,
        send_telegram: bool = True
    ) -> bool:
        """
        Send alert about screening results

        Args:
            results: List of screening results
            timeframe: Timeframe analyzed
            send_email: Whether to send email
            send_telegram: Whether to send Telegram

        Returns:
            True if at least one notification was sent
        """
        if not results:
            return False

        # Create message
        subject = f"🚀 Altcoin Screening Alert - {len(results)} Opportunities Found"

        # Plain text message
        text_message = self._create_text_alert(results, timeframe)

        # HTML message
        html_message = self._create_html_alert(results, timeframe)

        # Telegram message
        telegram_message = self._create_telegram_alert(results, timeframe)

        success = False

        # Send email
        if send_email:
            email_sent = await self.send_email(
                subject=subject,
                body=text_message,
                html=html_message
            )
            success = success or email_sent

        # Send Telegram
        if send_telegram:
            telegram_sent = await self.send_telegram(telegram_message)
            success = success or telegram_sent

        # Log alert
        if success:
            self._log_alert(
                alert_type='screening',
                message=subject,
                data={'count': len(results), 'timeframe': timeframe},
                sent_via='email' if send_email else '' + ',telegram' if send_telegram else ''
            )

        return success

    def _create_text_alert(self, results: List[dict], timeframe: str) -> str:
        """Create plain text alert message"""
        message = f"Altcoin Screening Results - {timeframe}\n"
        message += "=" * 60 + "\n\n"

        for i, result in enumerate(results[:10], 1):  # Top 10
            message += f"{i}. {result['symbol']}\n"
            message += f"   Score: {result['total_score']:.2f}\n"
            message += f"   Price: ${result['current_price']:.6f}\n"
            message += f"   BTC Ratio Change: {result['btc_ratio_change_pct']:.2f}%\n"
            message += f"   ETH Ratio Change: {result['eth_ratio_change_pct']:.2f}%\n"
            message += f"   Volume 24h: ${result['volume_24h']:,.0f}\n"

            signals = []
            if result['above_sma']:
                signals.append("Above SMA")
            if result['macd_golden_cross']:
                signals.append("MACD Golden Cross")
            if result['above_all_ema']:
                signals.append("Above All EMAs")
            if result['volume_surge']:
                signals.append("Volume Surge")
            if result['price_anomaly']:
                signals.append("Price Anomaly")

            if signals:
                message += f"   Signals: {', '.join(signals)}\n"

            message += "\n"

        return message

    def _create_html_alert(self, results: List[dict], timeframe: str) -> str:
        """Create HTML alert message"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .high-score {{ background-color: #d4edda; }}
                .signal {{ display: inline-block; padding: 2px 8px; margin: 2px;
                          background-color: #007bff; color: white; border-radius: 3px;
                          font-size: 12px; }}
            </style>
        </head>
        <body>
            <h2>🚀 Altcoin Screening Results - {timeframe}</h2>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Symbol</th>
                    <th>Score</th>
                    <th>Price</th>
                    <th>BTC Change</th>
                    <th>ETH Change</th>
                    <th>Volume 24h</th>
                    <th>Signals</th>
                </tr>
        """

        for i, result in enumerate(results[:10], 1):
            row_class = 'high-score' if result['total_score'] >= 70 else ''

            signals = []
            if result['above_sma']:
                signals.append('<span class="signal">Above SMA</span>')
            if result['macd_golden_cross']:
                signals.append('<span class="signal">MACD Cross</span>')
            if result['above_all_ema']:
                signals.append('<span class="signal">Above EMAs</span>')
            if result['volume_surge']:
                signals.append('<span class="signal">Volume Surge</span>')
            if result['price_anomaly']:
                signals.append('<span class="signal">Anomaly</span>')

            html += f"""
                <tr class="{row_class}">
                    <td>{i}</td>
                    <td><strong>{result['symbol']}</strong></td>
                    <td>{result['total_score']:.2f}</td>
                    <td>${result['current_price']:.6f}</td>
                    <td>{result['btc_ratio_change_pct']:.2f}%</td>
                    <td>{result['eth_ratio_change_pct']:.2f}%</td>
                    <td>${result['volume_24h']:,.0f}</td>
                    <td>{''.join(signals)}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        return html

    def _create_telegram_alert(self, results: List[dict], timeframe: str) -> str:
        """Create Telegram alert message"""
        message = f"🚀 <b>Altcoin Screening Alert</b>\n"
        message += f"📊 Timeframe: {timeframe}\n"
        message += f"🎯 Found {len(results)} opportunities\n\n"

        for i, result in enumerate(results[:5], 1):  # Top 5 for Telegram
            message += f"<b>{i}. {result['symbol']}</b>\n"
            message += f"💯 Score: {result['total_score']:.2f}\n"
            message += f"💰 Price: ${result['current_price']:.6f}\n"
            message += f"📈 BTC Change: {result['btc_ratio_change_pct']:.2f}%\n"
            message += f"📈 ETH Change: {result['eth_ratio_change_pct']:.2f}%\n"

            signals = []
            if result['above_sma']:
                signals.append("✅ Above SMA")
            if result['macd_golden_cross']:
                signals.append("⭐ MACD Cross")
            if result['above_all_ema']:
                signals.append("📊 Above EMAs")
            if result['volume_surge']:
                signals.append("📢 Volume Surge")

            if signals:
                message += "\n".join(signals) + "\n"

            message += "\n"

        return message

    def _log_alert(
        self,
        alert_type: str,
        message: str,
        data: dict,
        sent_via: str,
        symbol: str = None
    ):
        """Log alert to database"""
        try:
            alert = Alert(
                symbol=symbol or 'MULTIPLE',
                alert_type=alert_type,
                message=message,
                data=data,
                sent_via=sent_via,
                timestamp=datetime.utcnow()
            )
            self.db.add(alert)
            self.db.commit()
        except Exception as e:
            print(f"Failed to log alert: {e}")
            self.db.rollback()
