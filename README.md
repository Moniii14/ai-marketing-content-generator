AI-Powered Content Creator for Marketing

A multi-agent GenAI system that uses a Streamlit interface to automatically create, verify, score, and choose marketing content for various channels.
🔹Overview
In order to automate the creation of marketing content from a campaign brief, this project uses a modular, agent-based architecture. Even in the absence of live LLM API access, it is intended to be dependable, demo-ready, and functional.
🔹Important Features
- Channel-specific content creation (Email, SMS, Social) - Multi-agent pipeline (Audience, Content, Compliance, Variation, Quality Scoring, Memory)
Automated quality scoring and compliance verification; best-variant selection using predetermined metrics
The API's mock LLM fallback-independent performance
JSONL-based persistent memory; interactive Streamlit user interface with export capabilities (JSON and CSV)

🔹 Architecture [Agent Flow](agent_flow.jpg)

[Execution Flow] (execution_flow.jpeg)

🔹 Tech Stack: Python, LangChain, Streamlit, OpenAI (optional), JSON/CSV, and dotenv