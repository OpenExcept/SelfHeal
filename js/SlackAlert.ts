import { WebClient } from '@slack/web-api';

interface AlertOptions {
  functionName: string;
  error: Error;
  debugStatePath: string;
}

export class SlackAlert {
  private client: WebClient;
  private defaultChannel: string;

  constructor(slackToken: string, defaultChannel: string = '#alerts') {
    this.client = new WebClient(slackToken);
    this.defaultChannel = defaultChannel;
  }

  private getColorForSeverity(severity: 'info' | 'warning' | 'error'): string {
    const colors = {
      info: '#36a64f',    // green
      warning: '#ffa500', // orange
      error: '#ff0000'    // red
    };
    return colors[severity];
  }

  async sendAlert(options: AlertOptions): Promise<string | null> {
    try {
      const { functionName, error, debugStatePath } = options;

      const blocks = [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `🚨 Exception in function \`${functionName}\`\n*Type:* \`${error.constructor.name}\`\n*Message:* ${error.message}`
          }
        },
        {
          type: 'context',
          elements: [
            {
              type: 'mrkdwn',
              text: `*Severity:* error | *Time:* ${new Date().toISOString()}`
            }
          ]
        }
      ];

      const response = await this.client.chat.postMessage({
        channel: this.defaultChannel,
        blocks,
        attachments: [{ color: this.getColorForSeverity('error') }]
      });

      if (response.ok && response.ts) {
        await this.replyToThread(response.ts, debugStatePath);
        return response.ts;
      }

      return null;
    } catch (error) {
      console.error('Failed to send Slack alert:', error);
      return null;
    }
  }

  async replyToThread(threadTs: string, debugStatePath: string): Promise<void> {
    try {
      const viewerUrl = `https://selfheal.dev/demo?debug_path=${encodeURIComponent(debugStatePath)}`;
      
      await this.client.chat.postMessage({
        channel: this.defaultChannel,
        thread_ts: threadTs,
        blocks: [
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: `View debug state: <${viewerUrl}|Open in Viewer>`
            }
          }
        ],
        attachments: [{ color: this.getColorForSeverity('info') }]
      });
    } catch (error) {
      console.error('Failed to reply to thread:', error);
    }
  }
} 