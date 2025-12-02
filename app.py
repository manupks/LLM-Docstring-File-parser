import streamlit as st
from pathlib import Path

# Import your core modules
from ai_doc_layer.code_parser import find_python_files, extract_functions_from_file
from ai_doc_layer.doc_generator import DocGenerator
from ai_doc_layer.writer import inject_docstrings_into_file, write_module_markdown

st.set_page_config(page_title="AI Python Doc Generator", layout="wide")
st.title("AI Python Docstring Generator")

repo_path = st.text_input(
    "Python project folder (absolute path)", "", placeholder="C:/Users/yourname/project"
)

run_btn = st.button("Generate Docstrings")

if repo_path and run_btn:
    repo = Path(repo_path).resolve()
    st.write(f"Scanning: {repo}")
    files = find_python_files(repo)
    st.write(f"Found files: {len(files)}")

    doc_gen = DocGenerator()
    for file_path in files:
        st.write(f"Processing {file_path.name}")
        functions = extract_functions_from_file(file_path)
        func_docs = {}
        for func in functions:
            docstring = doc_gen.generate_docstring(func, file_path)
            func_docs[func.lineno] = docstring
            st.markdown(f"**Function:** `{func.name}`<br>**Docstring:**<br>{docstring}", unsafe_allow_html=True)

        inject_docstrings_into_file(file_path, func_docs)
        module_md = doc_gen.generate_module_overview(file_path, functions)
        write_module_markdown(repo, file_path, module_md, functions)
    st.success("Docstrings injected! Check your repo and ai_docs folder.")

st.markdown("---")
st.markdown("This tool uses a local LLM (e.g., TinyLlama) to generate documentation for your Python repo.")
