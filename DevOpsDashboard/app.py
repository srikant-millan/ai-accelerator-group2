import streamlit as st  # type: ignore[import-untyped]
import os
from dotenv import load_dotenv  # type: ignore[import-untyped]
import sys

# Add agents directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import multi-agent framework
try:
    from agents import MultiAgentOrchestrator
    MULTI_AGENT_AVAILABLE = True
except ImportError as e:
    MULTI_AGENT_AVAILABLE = False
    print(f"Multi-agent framework not available: {e}")

# Fallback to old system
from error_analyzer import ErrorAnalyzer
from notification_agents import SlackNotifier

# Optional JIRA import
try:
    from notification_agents import JIRANotifier
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    JIRANotifier = None

import tempfile

# Load environment variables from .env file
# Both Slack and JIRA will use the same .env file loaded here
# Try current directory first (DevOpsDashboard/.env), then parent directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
env_file_used = None
if os.path.exists(env_path):
    load_dotenv(env_path)
    env_file_used = env_path
else:
    # Fallback to parent directory
    parent_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(parent_env_path):
        load_dotenv(parent_env_path)
        env_file_used = parent_env_path
    else:
        # Default behavior - search for .env in current and parent directories
        load_dotenv()
        env_file_used = "auto-detected"

# Page configuration
st.set_page_config(
    page_title="Log Error Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'selected_solution' not in st.session_state:
    st.session_state.selected_solution = None
if 'log_content' not in st.session_state:
    st.session_state.log_content = None
if 'log_files' not in st.session_state:
    st.session_state.log_files = []
if 'classification_result' not in st.session_state:
    st.session_state.classification_result = None
if 'solutions' not in st.session_state:
    st.session_state.solutions = None
if 'use_multi_agent' not in st.session_state:
    st.session_state.use_multi_agent = True

def main():
    st.title("🔍 Log Error Analyzer & Notification System")
    st.markdown("Upload multiple log files to analyze errors using AI-powered multi-agent framework")
    
    # Multi-agent framework indicator
    if MULTI_AGENT_AVAILABLE:
        st.success("✅ Multi-Agent Framework (LangGraph) Enabled")
    else:
        st.warning("⚠️ Multi-Agent Framework not available, using fallback mode")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Enter your OpenRouter API key or set OPENAI_API_KEY environment variable. Get your key from https://openrouter.ai/"
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        st.divider()
        
        # Show which .env file is being used
        if env_file_used:
            st.caption(f"📁 Using .env: {os.path.basename(env_file_used) if env_file_used != 'auto-detected' else 'auto-detected'}")
        
        # Notification settings
        st.subheader("📢 Notification Settings")
        
        # Get Slack webhook from .env file (same .env as JIRA)
        slack_webhook_env = os.getenv("SLACK_WEBHOOK_URL", "")
        
        slack_enabled = st.checkbox("Enable Slack Notifications", value=bool(slack_webhook_env))
        slack_webhook = slack_webhook_env  # Default to .env value
        
        if slack_enabled:
            slack_webhook_input = st.text_input(
                "Slack Webhook URL (optional override)",
                type="password",
                value=slack_webhook_env,
                help="Leave empty to use SLACK_WEBHOOK_URL from .env file, or enter a different webhook URL"
            )
            if slack_webhook_input:
                slack_webhook = slack_webhook_input
            elif slack_webhook_env:
                slack_webhook = slack_webhook_env
            else:
                slack_webhook = None
        
        # Get JIRA config from .env file (same .env as Slack)
        jira_server_env = os.getenv("JIRA_SERVER", "")
        jira_email_env = os.getenv("JIRA_EMAIL", "")
        jira_token_env = os.getenv("JIRA_API_TOKEN", "")
        jira_project_env = os.getenv("JIRA_PROJECT_KEY", "")
        
        jira_configured = bool(jira_server_env and jira_email_env and jira_token_env and jira_project_env)
        jira_enabled = st.checkbox("Enable JIRA Notifications", value=jira_configured)
        jira_config = {}
        
        if jira_enabled:
            jira_config['server'] = st.text_input(
                "JIRA Server URL (optional override)",
                value=jira_server_env,
                help="Leave empty to use JIRA_SERVER from .env file"
            ) or jira_server_env
            
            jira_config['email'] = st.text_input(
                "JIRA Email (optional override)",
                value=jira_email_env,
                help="Leave empty to use JIRA_EMAIL from .env file"
            ) or jira_email_env
            
            jira_config['api_token'] = st.text_input(
                "JIRA API Token (optional override)",
                type="password",
                value=jira_token_env,
                help="Leave empty to use JIRA_API_TOKEN from .env file"
            ) or jira_token_env
            
            jira_config['project_key'] = st.text_input(
                "JIRA Project Key (optional override)",
                value=jira_project_env,
                help="Leave empty to use JIRA_PROJECT_KEY from .env file"
            ) or jira_project_env
            
            jira_issue_type_env = os.getenv("JIRA_ISSUE_TYPE", "")
            jira_config['issue_type'] = st.text_input(
                "JIRA Issue Type (optional override)",
                value=jira_issue_type_env or "Task",
                help="Leave empty to use JIRA_ISSUE_TYPE from .env file, or 'Task' as default. Common types: Task, Bug, Story"
            ) or jira_issue_type_env or "Task"
            
            # Test JIRA connection button
            st.divider()
            if st.button("🔍 Test JIRA Connection", key="test_jira_connection", use_container_width=True):
                if jira_config.get('server') and jira_config.get('email') and jira_config.get('api_token'):
                    if JIRA_AVAILABLE:
                        try:
                            with st.spinner("Testing JIRA connection..."):
                                notifier = JIRANotifier(
                                    server=jira_config['server'],
                                    email=jira_config['email'],
                                    api_token=jira_config['api_token']
                                )
                                test_result = notifier.test_connection(jira_config.get('project_key'))
                                
                                if test_result['success']:
                                    st.success(test_result['message'])
                                    for key, value in test_result.get('details', {}).items():
                                        st.info(f"**{key.replace('_', ' ').title()}:** {value}")
                                else:
                                    st.error(test_result['message'])
                                    for key, value in test_result.get('details', {}).items():
                                        if 'error' in key.lower() or '❌' in str(value):
                                            st.error(f"**{key.replace('_', ' ').title()}:** {value}")
                                        else:
                                            st.warning(f"**{key.replace('_', ' ').title()}:** {value}")
                        except Exception as e:
                            st.error(f"❌ Connection test failed: {str(e)}")
                    else:
                        st.warning("⚠️ JIRA package not installed")
                else:
                    st.warning("⚠️ Please fill in all JIRA credentials first")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "📊 Analysis Results", "📢 Send Notifications"])
    
    with tab1:
        st.header("Upload Log Files")
        
        # Multi-file upload support
        uploaded_files = st.file_uploader(
            "Choose log files (multiple files supported)",
            type=['log', 'txt', 'out', 'err', 'ndjson'],
            help="Upload one or more log files to analyze errors",
            key="file_uploader",
            accept_multiple_files=True
        )
        
        # Single file upload (for backward compatibility)
        if not uploaded_files:
            uploaded_file = st.file_uploader(
                "Or choose a single log file",
                type=['log', 'txt', 'out', 'err'],
                help="Upload a single log file",
                key="single_file_uploader"
            )
            if uploaded_file:
                uploaded_files = [uploaded_file]
        
        if uploaded_files:
            # Process multiple files
            log_files_data = []
            total_size = 0
            total_lines = 0
            
            for uploaded_file in uploaded_files:
                log_content = uploaded_file.read().decode('utf-8', errors='ignore')
                log_files_data.append({
                    'filename': uploaded_file.name,
                    'content': log_content
                })
                total_size += len(log_content)
                total_lines += len(log_content.splitlines())
            
            st.session_state.log_files = log_files_data
            if log_files_data:
                st.session_state.log_content = log_files_data[0]['content']  # Store first file for preview
            
            # Display file info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Files Uploaded", len(uploaded_files))
            with col2:
                st.metric("Total Size", f"{total_size:,} chars")
            with col3:
                st.metric("Total Lines", f"{total_lines:,}")
            with col4:
                file_names = [f.name for f in uploaded_files]
                with st.expander("📁 File Names"):
                    for name in file_names:
                        st.text(name)
            
            # Show preview of first file
            if log_files_data:
                with st.expander("📋 Log File Preview (First File)", expanded=True):
                    preview_text = log_files_data[0]['content'][:2000] if len(log_files_data[0]['content']) > 2000 else log_files_data[0]['content']
                    st.text_area(
                        "Preview", 
                        preview_text, 
                        height=300, 
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    if len(log_files_data[0]['content']) > 2000:
                        st.caption(f"Showing first 2000 characters of {len(log_files_data[0]['content']):,} total characters")
            
            st.divider()
            
            # Analyze button
            analyze_col1, analyze_col2 = st.columns([1, 3])
            with analyze_col1:
                analyze_clicked = st.button("🔍 Analyze Errors", type="primary", use_container_width=True)
            
            if analyze_clicked:
                if not api_key:
                    st.error("❌ Please enter your OpenRouter API key in the sidebar")
                else:
                    if MULTI_AGENT_AVAILABLE and st.session_state.use_multi_agent:
                        # Use multi-agent framework
                        with st.spinner("🤖 Multi-Agent Analysis in progress... This may take 30-60 seconds."):
                            try:
                                # Prepare JIRA config
                                jira_config_for_agent = {}
                                if jira_config.get('server'):
                                    jira_config_for_agent = jira_config.copy()
                                
                                # Initialize orchestrator
                                orchestrator = MultiAgentOrchestrator(
                                    api_key=api_key,
                                    slack_webhook=slack_webhook if slack_enabled else None,
                                    jira_config=jira_config_for_agent if jira_enabled else None
                                )
                                
                                # Run classification and solution finding
                                result = orchestrator.run_workflow(
                                    log_files=log_files_data,
                                    send_notifications=False
                                )
                                
                                st.session_state.classification_result = result.get('classification_result')
                                st.session_state.solutions = result.get('solutions')
                                st.session_state.analysis_result = {
                                    'error_type': result.get('classification_result', {}).get('aggregated_analysis', {}).get('primary_issue_category', 'Unknown'),
                                    'severity': result.get('classification_result', {}).get('aggregated_analysis', {}).get('overall_severity', 'Medium'),
                                    'causes': [{'title': f, 'description': f} for f in result.get('classification_result', {}).get('aggregated_analysis', {}).get('key_findings', [])],
                                    'solutions': result.get('solutions', [])
                                }
                                
                                if result.get('errors'):
                                    st.warning(f"⚠️ Some errors occurred: {', '.join(result.get('errors', []))}")
                                
                                st.success("✅ Multi-Agent Analysis complete! Check the 'Analysis Results' tab.")
                                st.info("💡 Switch to the 'Analysis Results' tab to view detailed findings.")
                            except Exception as e:
                                st.error(f"❌ Error during multi-agent analysis: {str(e)}")
                                st.exception(e)
                    else:
                        # Fallback to single file analysis
                        if len(log_files_data) > 1:
                            st.warning("⚠️ Multi-agent framework not available. Analyzing first file only.")
                        
                        with st.spinner("🤖 Analyzing log file with AI... This may take 10-30 seconds."):
                            try:
                                analyzer = ErrorAnalyzer(api_key)
                                result = analyzer.analyze_errors(log_files_data[0]['content'])
                                st.session_state.analysis_result = result
                                st.success("✅ Analysis complete! Check the 'Analysis Results' tab.")
                                st.info("💡 Switch to the 'Analysis Results' tab to view detailed findings.")
                            except Exception as e:
                                st.error(f"❌ Error during analysis: {str(e)}")
                                st.exception(e)
            
            # Show quick analysis if available
            if st.session_state.analysis_result:
                st.divider()
                st.subheader("📊 Quick Analysis Preview")
                quick_result = st.session_state.analysis_result
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Error Type:** {quick_result.get('error_type', 'Unknown')}")
                with col2:
                    severity = quick_result.get('severity', 'Unknown')
                    severity_color = {
                        'Critical': '🔴',
                        'High': '🟠',
                        'Medium': '🟡',
                        'Low': '🟢'
                    }.get(severity, '⚪')
                    st.info(f"**Severity:** {severity_color} {severity}")
                with col3:
                    # Quick notification buttons after analysis
                    notification_col1, notification_col2 = st.columns(2)
                    
                    with notification_col1:
                        # Quick Slack notification button
                        slack_webhook_env = os.getenv("SLACK_WEBHOOK_URL", "")
                        slack_webhook_quick = slack_webhook or slack_webhook_env
                        
                        if slack_webhook_quick and st.session_state.selected_solution:
                            if st.button("📢 Slack", key="upload_tab_slack", use_container_width=True, type="primary"):
                                try:
                                    with st.spinner("Sending to Slack..."):
                                        notifier = SlackNotifier(slack_webhook_quick)
                                        success = notifier.send_error_notification(
                                            error_type=quick_result.get('error_type'),
                                            severity=quick_result.get('severity'),
                                            causes=quick_result.get('causes', []),
                                            selected_solution=st.session_state.selected_solution
                                        )
                                        if success:
                                            st.success("✅ Sent to Slack!")
                                            st.balloons()
                                        else:
                                            st.error("❌ Failed to send")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        elif slack_webhook_quick:
                            st.info("💡 Select solution")
                        else:
                            st.info("💡 Config Slack")
                    
                    with notification_col2:
                        # Quick JIRA notification button
                        jira_server_env = os.getenv("JIRA_SERVER", "")
                        jira_email_env = os.getenv("JIRA_EMAIL", "")
                        jira_token_env = os.getenv("JIRA_API_TOKEN", "")
                        jira_project_env = os.getenv("JIRA_PROJECT_KEY", "")
                        
                        jira_issue_type_env = os.getenv("JIRA_ISSUE_TYPE", "")
                        jira_config_quick = {
                            'server': jira_config.get('server') or jira_server_env,
                            'email': jira_config.get('email') or jira_email_env,
                            'api_token': jira_config.get('api_token') or jira_token_env,
                            'project_key': jira_config.get('project_key') or jira_project_env,
                            'issue_type': jira_config.get('issue_type') or jira_issue_type_env or "Task"
                        }
                        
                        if JIRA_AVAILABLE and jira_config_quick.get('server') and jira_config_quick.get('email') and jira_config_quick.get('api_token') and jira_config_quick.get('project_key'):
                            if st.session_state.selected_solution:
                                if st.button("🎫 JIRA", key="upload_tab_jira", use_container_width=True, type="primary"):
                                    try:
                                        with st.spinner("Creating JIRA ticket..."):
                                            notifier = JIRANotifier(
                                                server=jira_config_quick['server'],
                                                email=jira_config_quick['email'],
                                                api_token=jira_config_quick['api_token']
                                            )
                                            ticket = notifier.create_error_ticket(
                                                project_key=jira_config_quick['project_key'],
                                                error_type=quick_result.get('error_type'),
                                                severity=quick_result.get('severity'),
                                                causes=quick_result.get('causes', []),
                                                selected_solution=st.session_state.selected_solution,
                                                log_content=st.session_state.log_content[:5000] if st.session_state.log_content else "",
                                                issue_type=jira_config_quick.get('issue_type', 'Task')
                                            )
                                            if ticket:
                                                st.success(f"✅ Ticket: {ticket.get('key', 'Unknown')}")
                                                st.balloons()
                                            else:
                                                st.error("❌ Failed")
                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")
                            else:
                                st.info("💡 Select solution")
                        elif JIRA_AVAILABLE:
                            st.info("💡 Config JIRA")
                        else:
                            st.info("💡 Install JIRA")
                st.caption("👉 Go to 'Analysis Results' tab for detailed breakdown")
    
    with tab2:
        st.header("Analysis Results")
        
        if st.session_state.analysis_result is None and st.session_state.classification_result is None:
            st.info("👆 Please upload and analyze log files in the 'Upload & Analyze' tab first")
        else:
            # Use multi-agent results if available, otherwise fallback to old format
            if st.session_state.classification_result:
                # Multi-agent framework results
                classification_result = st.session_state.classification_result
                aggregated_analysis = classification_result.get('aggregated_analysis', {})
                
                # Display aggregated results from multiple files
                st.subheader("📊 Aggregated Analysis (Multi-File)")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Files Processed", classification_result.get('files_processed', 0))
                with col2:
                    st.metric("Total Errors", classification_result.get('total_errors', 0))
                with col3:
                    severity_dist = classification_result.get('severity_distribution', {})
                    critical_count = severity_dist.get('Critical', 0)
                    st.metric("Critical Issues", critical_count)
                with col4:
                    aggregated_errors = classification_result.get('aggregated_errors', {})
                    st.metric("Unique Error Types", len(aggregated_errors))
                
                st.divider()
                
                # Issue Classification Cards
                st.subheader("🏷️ Issue Classification")
                
                error_type = aggregated_analysis.get('primary_issue_category', 'General Error')
                severity = aggregated_analysis.get('overall_severity', 'Medium')
                
                # Map category to icon
                category_icons = {
                    'Network Issue': '🌐',
                    'Database Issue': '💾',
                    'Security Issue': '🔒',
                    'Resource Issue': '💻',
                    'Code Issue': '💻',
                    'General Error': '⚠️'
                }
                category_icon = category_icons.get(error_type, '⚠️')
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">{category_icon}</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Category</p>
                        <p style="margin: 0; font-size: 14px; color: white;">{error_type}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    severity_colors = {
                        'Critical': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        'High': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                        'Medium': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
                        'Low': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
                    }
                    severity_color = severity_colors.get(severity, 'linear-gradient(135deg, #d3d3d3 0%, #a8a8a8 100%)')
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: {severity_color}; color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">📊</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Severity</p>
                        <p style="margin: 0; font-size: 14px; color: white;">{severity}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">🔍</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Error Types</p>
                        <p style="margin: 0; font-size: 14px; color: white;">{len(aggregated_errors)} Unique</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    solutions_count = len(st.session_state.solutions) if st.session_state.solutions else 0
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">💡</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Solutions</p>
                        <p style="margin: 0; font-size: 14px; color: white;">{solutions_count} Available</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # File-by-file breakdown
                st.subheader("📁 File-by-File Breakdown")
                file_results = classification_result.get('file_results', [])
                for file_result in file_results:
                    with st.expander(f"📄 {file_result.get('filename', 'Unknown')} - {file_result.get('error_count', 0)} errors"):
                        if file_result.get('summary'):
                            st.markdown(f"**Summary:** {file_result.get('summary')}")
                        if file_result.get('errors'):
                            st.markdown("**Errors:**")
                            for error in file_result.get('errors', [])[:5]:  # Show first 5
                                st.markdown(f"- **{error.get('error_type', 'Unknown')}** ({error.get('severity', 'Unknown')}) - {error.get('message', '')}")
                
                st.divider()
                
                # Aggregated errors
                st.subheader("🔍 Aggregated Error Types")
                if aggregated_errors:
                    for error_type_name, error_data in sorted(aggregated_errors.items(), key=lambda x: x[1].get('count', 0), reverse=True)[:10]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{error_type_name}**")
                            st.markdown(f"Severity: {error_data.get('severity', 'Unknown')}")
                            st.markdown(f"Files affected: {len(error_data.get('files', []))}")
                        with col2:
                            st.metric("Occurrences", error_data.get('count', 0))
                        st.markdown("---")
                
                st.divider()
                
                # Key findings
                st.subheader("🔍 Key Findings")
                key_findings = aggregated_analysis.get('key_findings', [])
                if key_findings:
                    for finding in key_findings:
                        st.info(f"• {finding}")
                else:
                    st.info("No specific findings identified")
                
                st.divider()
                
                # Risk assessment
                st.subheader("⚠️ Risk Assessment")
                risk_assessment = aggregated_analysis.get('risk_assessment', 'No risk assessment available')
                st.warning(risk_assessment)
                
                # Use solutions from solution agent
                result = {
                    'error_type': error_type,
                    'severity': severity,
                    'causes': [{'title': f, 'description': f} for f in key_findings],
                    'solutions': st.session_state.solutions or []
                }
            else:
                # Fallback to old format
                result = st.session_state.analysis_result
                error_type = result.get('error_type', 'Unknown')
                severity = result.get('severity', 'Unknown')
                
                # Issue Classification Cards for fallback mode
                st.subheader("🏷️ Issue Classification")
                
                # Create classification cards
                col1, col2, col3, col4 = st.columns(4)
                
                # Get issue category from analysis result, or determine from error type
                issue_category = result.get('issue_category', 'General Error')
                
                # Map category to icon
                category_icons = {
                    'Network Issue': '🌐',
                    'Database Issue': '💾',
                    'Security Issue': '🔒',
                    'Resource Issue': '💻',
                    'Code Issue': '💻',
                    'General Error': '⚠️'
                }
                category_icon = category_icons.get(issue_category, '⚠️')
                
                # Fallback: determine category from error type if not provided
                if issue_category == 'General Error' or not result.get('issue_category'):
                    error_lower = error_type.lower()
                    if any(keyword in error_lower for keyword in ['connection', 'network', 'timeout', 'socket']):
                        issue_category = "Network Issue"
                        category_icon = "🌐"
                    elif any(keyword in error_lower for keyword in ['database', 'sql', 'query', 'db']):
                        issue_category = "Database Issue"
                        category_icon = "💾"
                    elif any(keyword in error_lower for keyword in ['authentication', 'auth', 'permission', 'access']):
                        issue_category = "Security Issue"
                        category_icon = "🔒"
                    elif any(keyword in error_lower for keyword in ['memory', 'oom', 'out of memory']):
                        issue_category = "Resource Issue"
                        category_icon = "💻"
                    elif any(keyword in error_lower for keyword in ['syntax', 'parse', 'compile', 'code']):
                        issue_category = "Code Issue"
                        category_icon = "💻"
                
                with col1:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">{category_icon}</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Category</p>
                        <p style="margin: 0; font-size: 14px; color: white;">{issue_category}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    severity_colors = {
                        'Critical': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        'High': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                        'Medium': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
                        'Low': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
                    }
                    severity_color = severity_colors.get(severity, 'linear-gradient(135deg, #d3d3d3 0%, #a8a8a8 100%)')
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: {severity_color}; color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">📊</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Severity</p>
                        <p style="margin: 0; font-size: 14px; color: white;">{severity}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">🔍</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Error Type</p>
                        <p style="margin: 0; font-size: 12px; color: white; word-wrap: break-word;">{error_type[:30]}{'...' if len(error_type) > 30 else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    causes_count = len(result.get('causes', []))
                    solutions_count = len(result.get('solutions', []))
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; text-align: center;">
                        <h3 style="margin: 0; color: white;">📈</h3>
                        <p style="margin: 5px 0; font-weight: bold; color: white;">Analysis</p>
                        <p style="margin: 0; font-size: 14px; color: white;">{causes_count} Causes, {solutions_count} Solutions</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # Error Details Section
                st.subheader("📋 Error Details")
                
                # Error Type and Severity in a card
                detail_col1, detail_col2 = st.columns(2)
                with detail_col1:
                    with st.container():
                        st.markdown("### 🔍 Error Type")
                        st.info(error_type)
                with detail_col2:
                    with st.container():
                        st.markdown("### 📊 Severity Level")
                        severity_badge = {
                            'Critical': '🔴 Critical',
                            'High': '🟠 High',
                            'Medium': '🟡 Medium',
                            'Low': '🟢 Low'
                        }.get(severity, f'⚪ {severity}')
                        st.info(severity_badge)
                
                st.divider()
                
                # Display error causes in cards
                st.subheader("🔍 Possible Error Causes")
                causes = result.get('causes', [])
                if causes:
                    for i, cause in enumerate(causes, 1):
                        with st.expander(f"**Cause {i}: {cause.get('title', 'Unknown Cause')}**", expanded=(i == 1)):
                            st.markdown(f"**Description:**")
                            st.write(cause.get('description', 'No description available'))
                else:
                    st.warning("No causes identified in the analysis")
                
                st.divider()
            
            # Display solutions in cards
            st.subheader("💡 Recommended Solutions (Top 3 from Solution Agent)")
            solutions = result.get('solutions', [])
            
            if solutions:
                for i, solution in enumerate(solutions):
                    with st.container():
                        # Create a card-like container for each solution
                        rank = solution.get('rank', i + 1)
                        effectiveness = solution.get('effectiveness', 'Medium')
                        complexity = solution.get('complexity', 'Medium')
                        time_estimate = solution.get('time_estimate', 'Unknown')
                        risk_level = solution.get('risk_level', 'Medium')
                        
                        st.markdown(f"""
                        <div style="padding: 20px; border: 2px solid #e0e0e0; border-radius: 10px; margin: 10px 0; background: #f9f9f9;">
                            <h3 style="color: #667eea;">💡 Solution {rank}: {solution.get('title', 'Unknown Solution')}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([0.85, 0.15])
                        
                        with col1:
                            st.markdown(f"**Description:** {solution.get('description', 'No description')}")
                            
                            # Solution metadata
                            meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
                            with meta_col1:
                                eff_color = {'High': '🟢', 'Medium': '🟡', 'Low': '🔴'}.get(effectiveness, '⚪')
                                st.metric("Effectiveness", f"{eff_color} {effectiveness}")
                            with meta_col2:
                                comp_color = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}.get(complexity, '⚪')
                                st.metric("Complexity", f"{comp_color} {complexity}")
                            with meta_col3:
                                st.metric("Time Estimate", time_estimate)
                            with meta_col4:
                                risk_color = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}.get(risk_level, '⚪')
                                st.metric("Risk Level", f"{risk_color} {risk_level}")
                            
                            if 'prerequisites' in solution and solution['prerequisites']:
                                st.markdown("**Prerequisites:**")
                                for prereq in solution['prerequisites']:
                                    st.markdown(f"- {prereq}")
                            
                            if 'steps' in solution and solution['steps']:
                                st.markdown("**Implementation Steps:**")
                                for j, step in enumerate(solution['steps'], 1):
                                    st.markdown(f"{j}. {step}")
                            
                            if 'code_example' in solution and solution['code_example']:
                                with st.expander("💻 View Code Example"):
                                    st.code(solution['code_example'], language='python')
                        
                        with col2:
                            if st.button("✅ Select", key=f"select_{i}", use_container_width=True, type="primary"):
                                st.session_state.selected_solution = solution
                                st.success(f"✅ Solution {rank} selected!")
                                st.rerun()
                        
                        if i < len(solutions) - 1:
                            st.markdown("---")
                
                # Show selected solution status
                if st.session_state.selected_solution:
                    st.success(f"🎯 **Selected Solution:** {st.session_state.selected_solution.get('title', 'Unknown')}")
                    
                    # Quick action buttons
                    st.divider()
                    st.subheader("🚀 Quick Actions")
                    
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        # Quick Slack notification button
                        slack_webhook_env = os.getenv("SLACK_WEBHOOK_URL", "")
                        slack_webhook_quick = slack_webhook or slack_webhook_env
                        
                        if slack_webhook_quick:
                            if st.button("📢 Send to Slack", key="quick_slack", use_container_width=True, type="primary"):
                                try:
                                    with st.spinner("Sending to Slack..."):
                                        notifier = SlackNotifier(slack_webhook_quick)
                                        success = notifier.send_error_notification(
                                            error_type=result.get('error_type'),
                                            severity=result.get('severity'),
                                            causes=result.get('causes', []),
                                            selected_solution=st.session_state.selected_solution
                                        )
                                        if success:
                                            st.success("✅ Sent to Slack!")
                                            st.balloons()
                                        else:
                                            st.error("❌ Failed to send")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        else:
                            st.info("💡 Configure Slack webhook")
                    
                    with action_col2:
                        # Quick JIRA notification button
                        jira_server_env = os.getenv("JIRA_SERVER", "")
                        jira_email_env = os.getenv("JIRA_EMAIL", "")
                        jira_token_env = os.getenv("JIRA_API_TOKEN", "")
                        jira_project_env = os.getenv("JIRA_PROJECT_KEY", "")
                        
                        jira_issue_type_env = os.getenv("JIRA_ISSUE_TYPE", "")
                        jira_config_quick = {
                            'server': jira_config.get('server') or jira_server_env,
                            'email': jira_config.get('email') or jira_email_env,
                            'api_token': jira_config.get('api_token') or jira_token_env,
                            'project_key': jira_config.get('project_key') or jira_project_env,
                            'issue_type': jira_config.get('issue_type') or jira_issue_type_env or "Task"
                        }
                        
                        if JIRA_AVAILABLE and jira_config_quick.get('server') and jira_config_quick.get('email') and jira_config_quick.get('api_token') and jira_config_quick.get('project_key'):
                            if st.button("🎫 Create JIRA Ticket", key="quick_jira", use_container_width=True, type="primary"):
                                try:
                                    with st.spinner("Creating JIRA ticket..."):
                                        notifier = JIRANotifier(
                                            server=jira_config_quick['server'],
                                            email=jira_config_quick['email'],
                                            api_token=jira_config_quick['api_token']
                                        )
                                        ticket = notifier.create_error_ticket(
                                            project_key=jira_config_quick['project_key'],
                                            error_type=result.get('error_type'),
                                            severity=result.get('severity'),
                                            causes=result.get('causes', []),
                                            selected_solution=st.session_state.selected_solution,
                                            log_content=st.session_state.log_content[:5000] if st.session_state.log_content else "",
                                            issue_type=jira_config_quick.get('issue_type', 'Task')
                                        )
                                        if ticket:
                                            st.success(f"✅ Ticket: {ticket.get('key', 'Unknown')}")
                                            st.info(f"🔗 {ticket.get('url', 'N/A')}")
                                            st.balloons()
                                        else:
                                            st.error("❌ Failed to create")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                                    st.exception(e)
                        elif JIRA_AVAILABLE:
                            st.info("💡 Configure JIRA")
                        else:
                            st.info("💡 Install JIRA package")
                    
                    with action_col3:
                        st.info("📢 Go to 'Send Notifications' tab for more options")
            else:
                st.warning("No solutions found in the analysis")
    
    with tab3:
        st.header("Send Notifications")
        
        if (st.session_state.analysis_result is None and st.session_state.classification_result is None):
            st.info("👆 Please analyze log files first")
        elif st.session_state.selected_solution is None:
            st.info("👆 Please select a solution from the Analysis Results tab")
        else:
            # Get result data
            if st.session_state.classification_result:
                classification_result = st.session_state.classification_result
                aggregated_analysis = classification_result.get('aggregated_analysis', {})
                result = {
                    'error_type': aggregated_analysis.get('primary_issue_category', 'Unknown'),
                    'severity': aggregated_analysis.get('overall_severity', 'Medium'),
                    'causes': [{'title': f, 'description': f} for f in aggregated_analysis.get('key_findings', [])]
                }
            else:
                result = st.session_state.analysis_result
            
            solution = st.session_state.selected_solution
            
            st.subheader("📝 Notification Preview")
            
            # Display what will be sent
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Error Information:**")
                st.json({
                    "Error Type": result.get('error_type'),
                    "Severity": result.get('severity'),
                    "Selected Solution": solution.get('title'),
                    "Effectiveness": solution.get('effectiveness', 'N/A'),
                    "Complexity": solution.get('complexity', 'N/A')
                })
            
            with col2:
                st.markdown("**Solution Details:**")
                st.markdown(f"**Title:** {solution.get('title')}")
                st.markdown(f"**Description:** {solution.get('description')}")
                st.markdown(f"**Time Estimate:** {solution.get('time_estimate', 'N/A')}")
                st.markdown(f"**Risk Level:** {solution.get('risk_level', 'N/A')}")
            
            st.divider()
            
            # Notification buttons using multi-agent framework
            col1, col2 = st.columns(2)
            
            with col1:
                # Get Slack webhook from .env file or sidebar override
                slack_webhook_env = os.getenv("SLACK_WEBHOOK_URL", "")
                slack_webhook_to_use = slack_webhook or slack_webhook_env
                
                if slack_webhook_to_use:
                    st.markdown("### 📢 Slack Notification")
                    if st.button("📢 Send to Slack", key="notification_tab_slack", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Sending notification to Slack..."):
                                if MULTI_AGENT_AVAILABLE and api_key:
                                    # Use multi-agent notification agent
                                    from agents import NotificationAgent
                                    notification_agent = NotificationAgent(
                                        slack_webhook=slack_webhook_to_use,
                                        jira_config=None
                                    )
                                    notification_result = notification_agent.send_slack_notification(
                                        error_type=result.get('error_type'),
                                        severity=result.get('severity'),
                                        causes=result.get('causes', []),
                                        selected_solution=solution,
                                        aggregated_data=st.session_state.classification_result
                                    )
                                    
                                    if notification_result.get('success'):
                                        st.success("✅ Notification sent to Slack successfully!")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Failed: {notification_result.get('error', 'Unknown error')}")
                                else:
                                    # Fallback to direct notifier
                                    notifier = SlackNotifier(slack_webhook_to_use)
                                    success = notifier.send_error_notification(
                                        error_type=result.get('error_type'),
                                        severity=result.get('severity'),
                                        causes=result.get('causes', []),
                                        selected_solution=solution
                                    )
                                    if success:
                                        st.success("✅ Notification sent to Slack successfully!")
                                        st.balloons()
                                    else:
                                        st.error("❌ Failed to send notification to Slack")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.exception(e)
                    
                    # Show which webhook source is being used
                    webhook_source = "sidebar override" if slack_webhook and slack_webhook != slack_webhook_env else ".env file"
                    st.caption(f"📝 Using webhook from {webhook_source}")
                    st.info("💡 The notification will include error details, causes, and the selected solution.")
                else:
                    st.warning("⚠️ Slack webhook URL not configured")
                    st.info("💡 Set SLACK_WEBHOOK_URL in .env file or enable Slack in sidebar")
            
            with col2:
                # Get JIRA config from .env file or sidebar override
                jira_server_env = os.getenv("JIRA_SERVER", "")
                jira_email_env = os.getenv("JIRA_EMAIL", "")
                jira_token_env = os.getenv("JIRA_API_TOKEN", "")
                jira_project_env = os.getenv("JIRA_PROJECT_KEY", "")
                
                # Use sidebar config if available, otherwise use .env
                jira_issue_type_env = os.getenv("JIRA_ISSUE_TYPE", "")
                jira_config_to_use = {
                    'server': jira_config.get('server') or jira_server_env,
                    'email': jira_config.get('email') or jira_email_env,
                    'api_token': jira_config.get('api_token') or jira_token_env,
                    'project_key': jira_config.get('project_key') or jira_project_env,
                    'issue_type': jira_config.get('issue_type') or jira_issue_type_env or "Task"
                }
                
                if not JIRA_AVAILABLE:
                    st.warning("⚠️ JIRA package not installed. Install with: `pip install jira`")
                elif jira_config_to_use.get('server') and jira_config_to_use.get('email') and jira_config_to_use.get('api_token') and jira_config_to_use.get('project_key'):
                    st.markdown("### 🎫 JIRA Ticket")
                    if st.button("🎫 Create JIRA Ticket", key="notification_tab_jira", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Creating JIRA ticket..."):
                                if MULTI_AGENT_AVAILABLE and api_key:
                                    # Use multi-agent notification agent
                                    from agents import NotificationAgent
                                    notification_agent = NotificationAgent(
                                        slack_webhook=None,
                                        jira_config=jira_config_to_use
                                    )
                                    notification_result = notification_agent.create_jira_ticket(
                                        error_type=result.get('error_type'),
                                        severity=result.get('severity'),
                                        causes=result.get('causes', []),
                                        selected_solution=solution,
                                        log_content=st.session_state.log_content[:5000] if st.session_state.log_content else "",
                                        aggregated_data=st.session_state.classification_result
                                    )
                                    
                                    if notification_result.get('success'):
                                        st.success(f"✅ JIRA ticket created: {notification_result.get('ticket_key', 'Unknown')}")
                                        st.info(f"🔗 Link: {notification_result.get('ticket_url', 'N/A')}")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Failed: {notification_result.get('error', 'Unknown error')}")
                                else:
                                    # Fallback to direct notifier
                                    notifier = JIRANotifier(
                                        server=jira_config_to_use['server'],
                                        email=jira_config_to_use['email'],
                                        api_token=jira_config_to_use['api_token']
                                    )
                                    ticket = notifier.create_error_ticket(
                                        project_key=jira_config_to_use['project_key'],
                                        error_type=result.get('error_type'),
                                        severity=result.get('severity'),
                                        causes=result.get('causes', []),
                                        selected_solution=solution,
                                        log_content=st.session_state.log_content[:5000] if st.session_state.log_content else "",
                                        issue_type=jira_config_to_use.get('issue_type', 'Task')
                                    )
                                    if ticket:
                                        st.success(f"✅ JIRA ticket created: {ticket.get('key', 'Unknown')}")
                                        st.info(f"🔗 Link: {ticket.get('url', ticket.get('self', 'N/A'))}")
                                        st.balloons()
                                    else:
                                        st.error("❌ Failed to create JIRA ticket")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.exception(e)
                    
                    # Show which config source is being used
                    config_source = "sidebar override" if jira_config.get('server') else ".env file"
                    st.caption(f"📝 Using config from {config_source}")
                    st.info("💡 The ticket will include error details, causes, selected solution, and log preview.")
                else:
                    st.warning("⚠️ JIRA configuration incomplete")
                    st.info("💡 Set JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY in .env file or configure in sidebar")
            
            # Multi-agent notification option
            if MULTI_AGENT_AVAILABLE and api_key and slack_webhook_to_use and jira_config_to_use.get('server'):
                st.divider()
                st.subheader("🚀 Multi-Agent Notification")
                st.info("Send notifications using the multi-agent framework (both Slack and JIRA)")
                
                if st.button("📢 Send All Notifications", key="multi_agent_notify", type="primary", use_container_width=True):
                    try:
                        with st.spinner("Multi-agent notification in progress..."):
                            from agents import NotificationAgent
                            notification_agent = NotificationAgent(
                                slack_webhook=slack_webhook_to_use,
                                jira_config=jira_config_to_use if jira_config_to_use.get('server') else None
                            )
                            
                            notification_results = notification_agent.send_notifications(
                                error_type=result.get('error_type'),
                                severity=result.get('severity'),
                                causes=result.get('causes', []),
                                selected_solution=solution,
                                log_content=st.session_state.log_content[:5000] if st.session_state.log_content else "",
                                aggregated_data=st.session_state.classification_result,
                                send_slack=True,
                                send_jira=jira_config_to_use.get('server') is not None
                            )
                            
                            if notification_results.get('all_success'):
                                st.success("✅ All notifications sent successfully!")
                                if notification_results.get('slack') and notification_results['slack'].get('success'):
                                    st.info("✅ Slack notification sent")
                                if notification_results.get('jira') and notification_results['jira'].get('success'):
                                    st.info(f"✅ JIRA ticket created: {notification_results['jira'].get('ticket_key', 'Unknown')}")
                                st.balloons()
                            else:
                                if notification_results.get('slack') and not notification_results['slack'].get('success'):
                                    st.error(f"❌ Slack failed: {notification_results['slack'].get('error', 'Unknown')}")
                                if notification_results.get('jira') and not notification_results['jira'].get('success'):
                                    st.error(f"❌ JIRA failed: {notification_results['jira'].get('error', 'Unknown')}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.exception(e)

if __name__ == "__main__":
    main()

