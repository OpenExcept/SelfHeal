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

def get_analysis_cache_path(debug_state_path: Path) -> Path:
    """Get the path where the analysis cache should be stored."""
    cache_dir = Path("/root/analysis_cache")
    cache_dir.mkdir(exist_ok=True, parents=True)
    return cache_dir / f"{debug_state_path.stem}_analysis.txt"

def load_cached_analysis(debug_state_path: Path) -> str | None:
    """Load cached analysis if it exists."""
    cache_path = get_analysis_cache_path(debug_state_path)
    if cache_path.exists():
        try:
            return cache_path.read_text()
        except Exception as e:
            st.warning(f"Failed to load cached analysis: {e}")
    return None

def save_analysis_cache(debug_state_path: Path, analysis: str):
    """Save analysis result to cache."""
    cache_path = get_analysis_cache_path(debug_state_path)
    try:
        cache_path.write_text(analysis)
    except Exception as e:
        st.warning(f"Failed to cache analysis: {e}")

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
            
            # Try to load cached analysis first
            cached_analysis = load_cached_analysis(selected_file)
            if cached_analysis:
                st.markdown("### Cached Analysis")
                st.markdown(cached_analysis)
                if st.button("Reanalyze"):
                    with st.spinner("Reanalyzing with LLM..."):
                        analysis = debugger.analyze(str(selected_file))
                        save_analysis_cache(selected_file, analysis)
                        st.markdown(analysis)
            else:
                if st.button("Analyze Debug State"):
                    with st.spinner("Analyzing debug state with LLM..."):
                        analysis = debugger.analyze(str(selected_file))
                        save_analysis_cache(selected_file, analysis)
                        st.markdown(analysis)

if __name__ == "__main__":
    main()