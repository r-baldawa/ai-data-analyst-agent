import tempfile
import csv
import uuid
import streamlit as st
import pandas as pd
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.anthropic import Claude
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

# Function to preprocess and save the uploaded file
def preprocess_and_save(file):
    try:
        # Read the uploaded file into a DataFrame
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', na_values=['NA', 'N/A', 'missing'])
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file, na_values=['NA', 'N/A', 'missing'])
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None, None, None
        
        # Ensure string columns are properly quoted
        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].astype(str).replace({r'"': '""'}, regex=True)
        
        # Parse dates and numeric columns
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    # Keep as is if conversion fails
                    pass
        
        # Create a temporary file to save the preprocessed data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_path = temp_file.name
            # Save the DataFrame to the temporary CSV file with quotes around string fields
            df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)
        
        return temp_path, df.columns.tolist(), df  # Return the DataFrame as well
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None

# Streamlit app
st.title("📊 Data Analyst Agent")

# Sidebar for API keys
with st.sidebar:
    st.header("API Keys")
    anthropic_key = st.text_input("Enter your Anthropic API key:", type="password")
    if anthropic_key:
        st.session_state.anthropic_key = anthropic_key
        st.success("API key saved!")
    else:
        st.warning("Please enter your Anthropic API key to proceed.")

# File upload widget
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None and "anthropic_key" in st.session_state:
    # Only reprocess and reset the conversation when a *new* file is uploaded,
    # so the chat history and agent survive Streamlit's rerun-on-every-interaction model.
    if st.session_state.get("uploaded_file_name") != uploaded_file.name:
        temp_path, columns, df = preprocess_and_save(uploaded_file)
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.df = df
        st.session_state.columns = columns
        st.session_state.pop("agent", None)
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []

        if temp_path and columns and df is not None:
            duckdb_tools = DuckDbTools()
            duckdb_tools.load_local_csv_to_table(
                path=temp_path,
                table="uploaded_data",
            )
            st.session_state.duckdb_tools = duckdb_tools

    df = st.session_state.get("df")
    columns = st.session_state.get("columns")

    if df is not None and columns is not None:
        # Display the uploaded data as a table
        st.write("Uploaded Data:")
        st.dataframe(df)  # Use st.dataframe for an interactive table

        # Display the columns of the uploaded data
        st.write("Uploaded columns:", columns)

        # Build the agent once per uploaded file, with history enabled so
        # follow-up questions in this session carry prior turns as context.
        if "agent" not in st.session_state:
            st.session_state.agent = Agent(
                model=Claude(id="claude-sonnet-4-5-20250929", api_key=st.session_state.anthropic_key),
                tools=[st.session_state.duckdb_tools, PandasTools()],
                system_message="You are an expert data analyst. Use the 'uploaded_data' table to answer user queries. Generate SQL queries using DuckDB tools to solve the user's query. Provide clear and concise answers with the results.",
                db=InMemoryDb(),
                add_history_to_context=True,
                num_history_runs=5,
                markdown=True,
            )

        # Replay prior turns so the chat looks continuous across reruns
        for turn in st.session_state.chat_history:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])

        # Chat-style input so each question can build on earlier ones
        user_query = st.chat_input("Ask a question about the data...")

        if user_query:
            with st.chat_message("user"):
                st.markdown(user_query)
            st.session_state.chat_history.append({"role": "user", "content": user_query})

            with st.chat_message("assistant"):
                with st.spinner("Processing your query..."):
                    try:
                        response = st.session_state.agent.run(
                            user_query,
                            session_id=st.session_state.session_id,
                        )
                        response_content = response.content if hasattr(response, "content") else str(response)
                    except Exception as e:
                        response_content = (
                            f"Error generating response from the agent: {e}\n\n"
                            "Please try rephrasing your query or check if the data format is correct."
                        )
                st.markdown(response_content)
            st.session_state.chat_history.append({"role": "assistant", "content": response_content})