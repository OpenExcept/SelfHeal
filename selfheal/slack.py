import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime

class SlackAlertBot:
    def __init__(self, slack_token, default_channel="#alerts"):
        """
        Initialize the Slack bot with authentication token and default channel
        
        Args:
            slack_token (str): Slack Bot User OAuth Token
            default_channel (str): Default channel to send messages to
        """
        self.client = WebClient(token=slack_token)
        self.default_channel = default_channel
        
    def send_alert(self, message, channel=None, severity="info"):
        """
        Send an alert message to Slack
        
        Args:
            message (str): The message to send
            channel (str): Override the default channel
            severity (str): One of "info", "warning", "error"
        """
        # Set color based on severity
        colors = {
            "info": "#36a64f",    # green
            "warning": "#ffa500",  # orange
            "error": "#ff0000"     # red
        }
        
        # Construct the message block
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:* {severity} | *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        try:
            # Send the message
            response = self.client.chat_postMessage(
                channel=channel or self.default_channel,
                blocks=blocks,
                attachments=[{"color": colors.get(severity, colors["info"])}]
            )
            return response
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            raise

    def reply_to_thread(self, thread_ts, message, channel=None, severity="info"):
        """
        Reply to an existing Slack thread
        
        Args:
            thread_ts (str): Timestamp of the parent message to reply to
            message (str): The message to send
            channel (str): Override the default channel
            severity (str): One of "info", "warning", "error"
        """
        colors = {
            "info": "#36a64f",    # green
            "warning": "#ffa500",  # orange
            "error": "#ff0000"     # red
        }
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        try:
            response = self.client.chat_postMessage(
                channel=channel or self.default_channel,
                thread_ts=thread_ts,
                blocks=blocks,
                attachments=[{"color": colors.get(severity, colors["info"])}]
            )
            return response
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            raise

# Example usage
if __name__ == "__main__":
    # Load token from environment variable
    SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    
    # Initialize bot
    bot = SlackAlertBot(SLACK_TOKEN)
    
    # Send different types of alerts
    bot.send_alert("✅ System is running normally", severity="info")
    bot.send_alert("⚠️ High CPU usage detected (85%)", severity="warning")
    bot.send_alert("🚨 Database connection failed!", severity="error")
    
    # Send an initial message and then reply to it
    initial_message = bot.send_alert("🔄 Starting backup process...")
    thread_ts = initial_message['ts']
    bot.reply_to_thread(thread_ts, "📦 Backup completed successfully!", severity="info")