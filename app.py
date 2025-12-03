import streamlit as st
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from ai_doc_layer.code_parser import find_python_files, extract_functions_from_file
from ai_doc_layer.doc_generator import DocGenerator
from ai_doc_layer.writer import inject_docstrings_into_file, write_module_markdown
from ai_doc_layer.visualizer import UMLGenerator
from ai_doc_layer.ask_cli import CodebaseAssistant


st.set_page_config(page_title="AI Doc Assistant", layout="wide")

st.title("🧠 AI Python Documentation Assistant")
tab1, tab2, tab3 = st.tabs(["📘 Docstrings", "📊 Visualizer", "💬 Chat"])

# ---------------------------------------------------------
# TAB 1 — DOCSTRING GENERATOR WITH LIVE FUNCTION UPDATES
# ---------------------------------------------------------
with tab1:
    st.subheader("📘 Auto-generate docstrings with real-time updates")

    repo_path = st.text_input("Project folder:", "")

    run_btn = st.button("Generate Docstrings")

    if repo_path and run_btn:
        repo = Path(repo_path).resolve()

        if not repo.exists():
            st.error("❌ Path does not exist.")
        else:
            files = find_python_files(repo)
            total_files = len(files)

            st.info(f"🔍 Found **{total_files}** Python files.")

            doc_gen = DocGenerator()

            file_progress = st.progress(0, text="Starting…")

            # Container to update “current function”
            status_box = st.empty()

            # Container for all file logs
            file_log_container = st.container()

            for file_index, file_path in enumerate(files, start=1):

                file_progress.progress(
                    file_index / total_files,
                    text=f"Processing file {file_index}/{total_files}: {file_path.name}"
                )

                # Expandable section for each file
                with file_log_container.expander(f"📂 {file_path.name}", expanded=False):
                    functions = extract_functions_from_file(file_path)
                    total_funcs = len(functions)

                    st.write(f"📌 Found `{total_funcs}` functions.")

                    func_progress = st.progress(0)
                    func_count = 0

                    func_docs = {}

                    for func in functions:
                        func_count += 1

                        # LIVE STATUS UPDATE
                        status_box.markdown(
                            f"### 🔧 Processing function: **`{func.name}`** in `{file_path.name}`"
                        )

                        # Function progress bar
                        func_progress.progress(func_count / total_funcs)

                        # Generate docstring
                        doc = doc_gen.generate_docstring(func, file_path)
                        func_docs[func.lineno] = doc

                        # Show each result interactively
                        st.success(f"✔ Generated docstring for `{func.name}`")
                        st.code(doc, language="python")

                    # Inject docstrings into file
                    inject_docstrings_into_file(file_path, func_docs)
                    module_md = doc_gen.generate_module_overview(file_path, functions)
                    write_module_markdown(repo, file_path, module_md, functions)

            status_box.markdown("### 🎉 Completed all files!")
            st.success("Docstring generation completed successfully!")



# ---------------------------------------------------------
# TAB 2 — INTERACTIVE GRAPH VISUALIZER
# ---------------------------------------------------------
with tab2:
    st.subheader("📊 Structured UML Diagram")

    repo_path_uml = st.text_input("Folder:", key="uml")

    if st.button("Generate UML"):
        repo = Path(repo_path_uml)
        out_file = repo / "ai_docs" / "uml.png"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        uml = UMLGenerator()
        with st.spinner("Generating UML diagram..."):
            uml.generate(repo, out_file)

        st.success("UML diagram generated!")
        st.image(str(out_file))



# ---------------------------------------------------------
# TAB 3 — CHAT WITH CODEBASE
# ---------------------------------------------------------
with tab3:
    st.subheader("💬 Ask your codebase")
    repo_c = st.text_input("Project folder:", key="chat")
    q = st.text_area("Question:")

    if st.button("Ask"):
        assistant = CodebaseAssistant(Path(repo_c))
        with st.spinner("Thinking..."):
            ans = assistant.ask(q)
        st.success(ans)
