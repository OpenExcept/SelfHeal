import streamlit as st
import json
from pathlib import Path
from selfheal import FunctionDebugger
from urllib.parse import unquote

def load_debug_state(file_path: str) -> dict:
    """Load debug state from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading debug state: {str(e)}")
        return {}

def main():
    st.set_page_config(page_title="Debug State Viewer", layout="wide")
    st.title("Debug State Viewer & Analyzer")

    # Initialize debugger
    debugger = FunctionDebugger()
    
    # Check for debug_path in query parameters using the new API
    direct_debug_path = st.query_params.get("debug_path", None)
    
    # Get list of debug state files
    debug_files = list(Path(debugger.dump_dir).glob("*.json"))
    
    if not debug_files:
        st.warning("No debug state files found.")
        return
    
    # If direct_debug_path is provided, find it in the list or show error
    selected_file = None
    if direct_debug_path:
        direct_path = Path(unquote(direct_debug_path))
        if direct_path in debug_files:
            selected_file = direct_path
        else:
            st.error(f"Debug state file not found: {direct_path}")
    
    # Only show file selector if no direct path or file not found
    if not selected_file:
        selected_file = st.selectbox(
            "Select Debug State File",
            debug_files,
            format_func=lambda x: x.name
        )

    if selected_file:
        # Create two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Raw Debug State")
            debug_state = load_debug_state(selected_file)
            st.json(debug_state)
        
        with col2:
            st.header("Analysis")
            if st.button("Analyze Debug State"):
                with st.spinner("Analyzing debug state with LLM..."):
                    analysis = debugger.analyze(str(selected_file))
                    st.markdown(analysis)

if __name__ == "__main__":
    main()