#!/usr/bin/env python3
"""
Bot monitoring script with email alerts
"""

import subprocess
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import requests
import time

# Load email configuration
EMAIL_ENV_FILE = '/home/ubuntu/social-media-archive-project/.email_env'
if os.path.exists(EMAIL_ENV_FILE):
    with open(EMAIL_ENV_FILE) as f:
        for line in f:
            if line.startswith('export '):
                key, value = line.replace('export ', '').strip().split('=', 1)
                os.environ[key] = value.strip('"')

# Configure settings
BOT_NAME = "social-media-bot"
MEDIA_SERVER_NAME = "media-server"
CHECK_INTERVAL = 300  # Check every 5 minutes
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_TELEGRAM_CHAT_ID')

# Email settings
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/social-media-archive-project/logs/monitor.log'),
        logging.StreamHandler()
    ]
)

def check_service_status(service_name):
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except Exception as e:
        logging.error(f"Error checking {service_name} status: {e}")
        return False

def check_bot_responding():
    """Check if the bot is responding to Telegram API"""
    if not TELEGRAM_BOT_TOKEN:
        return True  # Skip if no token
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error checking bot API: {e}")
        return False

def send_email_alert(subject, body):
    """Send alert via Gmail"""
    if not EMAIL_ENABLED:
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = f"[Bot Alert] {subject}"
        
        html_body = f"""
        <html>
        <body>
            <h2>Social Media Archive Bot Alert</h2>
            <hr>
            <pre>{body}</pre>
            <hr>
            <p><small>Sent from monitoring system at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</small></p>
            <p><small>Server: ov-ab103a.infomaniak.ch</small></p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
            
        logging.info(f"Email alert sent to {EMAIL_TO}")
        
    except Exception as e:
        logging.error(f"Error sending email: {e}")

def restart_service(service_name):
    """Attempt to restart a service"""
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', service_name], check=True)
        logging.info(f"{service_name} restarted successfully")
        return True
    except Exception as e:
        logging.error(f"Error restarting {service_name}: {e}")
        return False

def main():
    """Main monitoring loop"""
    logging.info("Starting bot monitor...")
    logging.info(f"Email alerts: {'Enabled' if EMAIL_ENABLED else 'Disabled'}")
    logging.info(f"Monitoring: {BOT_NAME}, {MEDIA_SERVER_NAME}")
    
    consecutive_failures = {}
    last_alert_time = {}
    ALERT_COOLDOWN = 3600  # Don't send alerts more than once per hour
    
    # Send startup notification
    if EMAIL_ENABLED:
        send_email_alert(
            "Monitor Started",
            "Bot monitoring system has started successfully.\n\n"
            f"Monitoring services:\n- {BOT_NAME}\n- {MEDIA_SERVER_NAME}\n\n"
            f"Email alerts: Enabled\n"
            f"Check interval: {CHECK_INTERVAL} seconds"
        )
    
    while True:
        try:
            services_to_check = [
                (BOT_NAME, True),  # Check API for bot
                (MEDIA_SERVER_NAME, False)  # No API check for media server
            ]
            
            for service_name, check_api in services_to_check:
                service_running = check_service_status(service_name)
                api_responding = check_bot_responding() if check_api else True
                
                if not service_running or not api_responding:
                    consecutive_failures[service_name] = consecutive_failures.get(service_name, 0) + 1
                    
                    issue = []
                    if not service_running:
                        issue.append("Service not running")
                    if not api_responding:
                        issue.append("Bot not responding to API")
                    
                    message = f"Service: {service_name}\n"
                    message += f"Issue: {', '.join(issue)}\n"
                    message += f"Failure count: {consecutive_failures[service_name]}\n"
                    message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    
                    logging.warning(message)
                    
                    # Try to restart after 2 consecutive failures
                    if consecutive_failures[service_name] >= 2:
                        logging.info(f"Attempting automatic restart of {service_name}...")
                        if restart_service(service_name):
                            message += f"\n\n✅ {service_name} restarted successfully!"
                            consecutive_failures[service_name] = 0
                        else:
                            message += f"\n\n❌ Failed to restart {service_name}!"
                    
                    # Send alerts (with cooldown)
                    current_time = time.time()
                    last_time = last_alert_time.get(service_name, 0)
                    if current_time - last_time > ALERT_COOLDOWN:
                        send_email_alert(f"{service_name} Down", message)
                        last_alert_time[service_name] = current_time
                    
                else:
                    if consecutive_failures.get(service_name, 0) > 0:
                        recovery_msg = f"✅ {service_name} is back online and healthy!"
                        logging.info(recovery_msg)
                        send_email_alert(f"{service_name} Recovered", recovery_msg)
                    consecutive_failures[service_name] = 0
                
        except Exception as e:
            logging.error(f"Monitor error: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
