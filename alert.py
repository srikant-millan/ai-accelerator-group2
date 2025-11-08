from slack_sdk import WebClient
from jira import JIRA
from dotenv import load_dotenv
import os

load_dotenv()

slack = WebClient(token=os.getenv("SLACK_TOKEN"))
jira = JIRA(server=os.getenv("JIRA_URL"), basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")))

def send_alerts(summary, errors):
    # Slack
    error_text = "\n".join([e['text'][:100] for e in errors[:3]])
    slack.chat_postMessage(
        channel=os.getenv("SLACK_CHANNEL"),
        text=f"🚨 INCIDENT ALERT\n*Root Cause*: {summary}\n*Errors*:\n{error_text}"
    )
    
    # Jira
    desc = f"{summary}\n\nTop errors:\n" + "\n".join([e['text'] for e in errors[:10]])
    issue = jira.create_issue(
        project='KAN',  # Change to your project key
        summary="Auto Incident: " + summary[:50],
        description=desc,
        issuetype={'name': 'Task'}
    )
    return f"{os.getenv('JIRA_URL')}/browse/{issue.key}"