# 🔍 Log Error Analyzer & Notification System

A powerful Streamlit application that analyzes log files using AI (OpenAI) to identify errors, provide root cause analysis, and suggest actionable solutions. The app also includes notification agents for Slack and JIRA integration.

## ✨ Features

- **📤 Log File Upload**: Upload and analyze log files (.log, .txt, .out, .err)
- **🤖 AI-Powered Analysis**: Uses OpenAI GPT-4 to analyze errors and provide insights
- **🔍 Error Detection**: Automatically identifies error patterns, exceptions, and failures
- **💡 Smart Solutions**: Provides 3 actionable solutions with step-by-step instructions
- **📊 Interactive UI**: Clean, modern interface with tabbed navigation
- **📢 Slack Integration**: Send error notifications directly to Slack channels
- **🎫 JIRA Integration**: Create JIRA tickets automatically with error details

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (tested with Python 3.14)
- OpenAI API key
- (Optional) Slack webhook URL for notifications
- (Optional) JIRA credentials for ticket creation

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd ai-accelerator-group2
   ```

2. **Activate your virtual environment:**
   ```bash
   source myenv/bin/activate  # On macOS/Linux
   # or
   myenv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

5. **Verify your environment (optional but recommended):**
   ```bash
   python check_environment.py
   ```
   This will check if all required packages are installed correctly.

6. **Run the Streamlit app:**
   
   **Option 1: Use the startup script (recommended):**
   ```bash
   ./run_app.sh
   ```
   
   **Option 2: Manual activation:**
   ```bash
   # Make sure virtual environment is activated
   source myenv/bin/activate
   
   # Verify you're using the correct Python
   which python  # Should show: .../myenv/bin/python
   
   # Run Streamlit
   streamlit run app.py
   ```

7. **Open your browser:**
   The app will automatically open at `http://localhost:8501`

**⚠️ Important:** If you get a "JIRA package is not installed" error, make sure:
- Your virtual environment is activated (`source myenv/bin/activate`)
- You're running Streamlit from within the activated environment
- The Python path shown in the error matches your virtual environment path

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (or use the sidebar in the app):

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional - JIRA Integration
JIRA_SERVER=https://yourcompany.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=PROJ
JIRA_ISSUE_TYPE=Task
```

### Getting API Keys

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste into the app sidebar or `.env` file

#### Slack Webhook URL
1. Go to your Slack workspace
2. Navigate to Apps → Incoming Webhooks
3. Create a new webhook
4. Select the channel where notifications should be sent
5. Copy the webhook URL

#### JIRA API Token
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label and copy the token
4. Use your JIRA email and this token for authentication

## 📖 Usage

### Step 1: Upload Log File
1. Click on the "Upload & Analyze" tab
2. Click "Browse files" or drag and drop a log file
3. Supported formats: `.log`, `.txt`, `.out`, `.err`

### Step 2: Analyze Errors
1. Enter your OpenAI API key in the sidebar (if not in `.env`)
2. Click "🔍 Analyze Errors" button
3. Wait for AI analysis to complete (usually 10-30 seconds)

### Step 3: Review Analysis
1. Navigate to "Analysis Results" tab
2. Review:
   - Error type and severity
   - Possible causes
   - 3 recommended solutions
3. Click "✅ Select" on your preferred solution

### Step 4: Send Notifications (Optional)
1. Configure Slack/JIRA in the sidebar
2. Navigate to "Send Notifications" tab
3. Review the notification preview
4. Click "📢 Send to Slack" or "🎫 Create JIRA Ticket"

## 🏗️ Project Structure

```
ai-accelerator-group2/
├── app.py                    # Main Streamlit application
├── error_analyzer.py         # LLM-based error analysis module
├── notification_agents.py   # Slack and JIRA notification agents
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .env.example             # Environment variables template
└── myenv/                   # Virtual environment (gitignored)
```

## 🔧 Technical Details

### Error Analyzer
- Uses OpenAI GPT-4o-mini for cost-effective analysis
- Extracts error lines using keyword matching
- Provides structured JSON responses with:
  - Error type and severity
  - Root cause analysis
  - 3 actionable solutions with code examples

### Notification Agents

#### Slack Notifier
- Sends formatted messages with error details
- Color-coded by severity (Critical=Red, High=Orange, etc.)
- Includes causes, selected solution, and implementation steps

#### JIRA Notifier
- Creates bug tickets automatically
- Maps severity to JIRA priority
- Includes full error analysis and log preview
- Supports adding comments to existing tickets

## 🐛 Troubleshooting

### "Please enter your OpenAI API key"
- Enter your API key in the sidebar
- Or set `OPENAI_API_KEY` in `.env` file

### "Failed to connect to JIRA"
- Verify JIRA server URL
- Check email and API token are correct
- Ensure API token is valid (not expired)

### "Slack notification failed"
- Verify webhook URL is correct
- Check Slack webhook is active
- Ensure channel permissions allow webhooks

### Analysis takes too long
- Large log files may take longer
- Check your OpenAI API quota
- Try analyzing smaller log files first

## 📝 Example Log Files

The app works with any text-based log file. Common formats:
- Application logs
- Server logs
- Error logs
- Stack traces
- System logs

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests.

## 📄 License

This project is open source and available for use.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenAI](https://openai.com/)
- Uses [Slack SDK](https://slack.dev/python-slack-sdk/) and [JIRA Python](https://jira.readthedocs.io/)

---

**Made with ❤️ for efficient error analysis and debugging**

