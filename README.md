# 📊 AI Data Analyst Agent (Claude edition)

An AI data analysis agent built using the [Agno](https://github.com/agno-agi/agno) agent framework and Anthropic's Claude Sonnet model. Upload a CSV or Excel file and ask questions about it in natural language — the agent generates DuckDB SQL under the hood to answer your questions, and remembers prior turns in the conversation so follow-up questions carry context.

Adapted from the [ai_data_analysis_agent](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/starter_ai_agents/ai_data_analysis_agent) example in [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps), swapped from OpenAI to Claude and extended with multi-turn chat.

## Features

- 📤 **File upload**: CSV and Excel, with automatic type/date inference
- 💬 **Natural language queries**: translated into DuckDB SQL under the hood
- 🧠 **Multi-turn context**: follow-up questions build on prior turns in the same session
- 🎯 **Chat-style Streamlit UI**

## Setup

```bash
git clone https://github.com/r-baldawa/ai-data-analyst-agent.git
cd ai-data-analyst-agent

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run ai_data_analyst.py
```

Enter your [Anthropic API key](https://console.anthropic.com/) in the sidebar, upload a CSV/Excel file, then ask questions about your data in the chat box.

## Notes

- Chat history is kept in-memory (`InMemoryDb`) — it resets when the server restarts. Swap in a persistent Agno DB backend for durability across restarts.
- Data stays local except for what's sent to Anthropic's API as part of answering your queries (SQL results, aggregates) — see Agno's `DuckDbTools` for exactly what that includes before uploading sensitive data.
