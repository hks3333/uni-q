import os
import csv
import streamlit as st
import requests
from io import StringIO

# Predefined tags
PREDEFINED_TAGS = ["Textbook", "Lecture Notes", "Research Paper", "Policy", "Announcement", "Notice", "Rulebook", "Other"]

# Predefined departments
DEPARTMENTS = [
    "Department of Computer Science",
    "Department of Mechanical Engineering",
    "Department of Electrical Engineering",
    "Department of Civil Engineering",
    "Department of Mathematics",
    "Department of Physics",
    "Department of Chemistry",
    "Department of Humanities",
]

# Predefined semesters
SEMESTERS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "Supply"]

# Always use the parent directory's documents folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

st.title("PDF Upload and Management")

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "uploaded_files_session" not in st.session_state:
    st.session_state.uploaded_files_session = []
if "edited_files_session" not in st.session_state:
    st.session_state.edited_files_session = []
if "deleted_files_session" not in st.session_state:
    st.session_state.deleted_files_session = []

st.sidebar.title("Admin Portal")
if st.sidebar.button("Home"):
    st.session_state.page = "Home"
if st.sidebar.button("Upload Files"):
    st.session_state.page = "Upload Files"
if st.sidebar.button("Edit Existing Files"):
    st.session_state.page = "Edit Existing Files"
if st.sidebar.button("View Session Actions"):
    st.write("**Uploaded Files:**", st.session_state.uploaded_files_session)
    st.write("**Edited Files:**", st.session_state.edited_files_session)
    st.write("**Deleted Files:**", st.session_state.deleted_files_session)

def save_to_local(file, file_path):
    with open(file_path, "wb") as f:
        f.write(file.read())

def save_metadata_csv(file_name, departments, semesters, tags):
    if "All" in departments:
        departments = DEPARTMENTS
    if "All" in semesters:
        semesters = SEMESTERS
    metadata_path = os.path.join(DOCUMENTS_DIR, f"{file_name}.csv")
    with open(metadata_path, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
    writer.writerow(["file_name", "departments", "semesters", "tags"])
    writer.writerow([
        file_name,
        ",".join(departments),
        ",".join(semesters),
        ",".join(tags)
    ])

def homepage():
    st.write("Welcome to the PDF Upload and Management System!")
    st.write("Use the navigation sidebar to switch between pages.")

def upload_page():
    st.write("### Upload PDFs")
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        st.subheader("Uploaded PDFs")
        cols = st.columns(2)
        for i, uploaded_file in enumerate(uploaded_files):
            with cols[i % 2]:
                st.write(f"**File {i + 1}**")
                file_name = uploaded_file.name.replace(".pdf", "")
                new_name = st.text_input(f"Name for File {i + 1}", value=file_name, key=f"name_{i}")
                departments = st.multiselect(
                    f"Department(s) for File {i + 1}",
                    options=["All"] + DEPARTMENTS,
                    default=[],
                    key=f"dept_{i}"
                )
                semesters = st.multiselect(
                    f"Semester(s) for File {i + 1}",
                    options=["All"] + SEMESTERS,
                    default=[],
                    key=f"sem_{i}"
                )
                tags = st.multiselect(
                    f"Tags for File {i + 1}",
                    options=PREDEFINED_TAGS,
                    default=[],
                    key=f"tags_{i}"
                )
                st.write("---")
    if st.button("Upload All Files"):
        if uploaded_files:
            for i, uploaded_file in enumerate(uploaded_files):
                new_name = st.session_state[f"name_{i}"]
                new_file_name = f"{new_name}.pdf"
                pdf_path = os.path.join(DOCUMENTS_DIR, new_file_name)
                uploaded_file.seek(0)
                save_to_local(uploaded_file, pdf_path)
                st.success(f"File {new_file_name} saved locally.")
                st.session_state.uploaded_files_session.append(new_file_name)
                try:
                    save_metadata_csv(
                            new_name,
                            st.session_state[f"dept_{i}"],
                            st.session_state[f"sem_{i}"],
                        st.session_state[f"tags_{i}"]
                        )
                    st.success(f"Metadata for {new_file_name} saved locally.")
                except Exception as e:
                    st.error(f"Error saving metadata for {new_file_name}: {e}")
        else:
            st.warning("No files uploaded.")

def edit_page():
    st.write("### Edit Existing Files")
    files = [f for f in os.listdir(DOCUMENTS_DIR) if f.endswith(".pdf")]
    if not files:
        st.warning("No files found in the local documents directory.")
        return
    selected_file = st.selectbox("Select a file to edit", files, index=None)
    if selected_file:
        metadata_file = selected_file.replace(".pdf", ".csv")
        metadata_path = os.path.join(DOCUMENTS_DIR, metadata_file)
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
            headers = next(reader)
            file_name, departments, semesters, tags = next(reader)
            departments = departments.split(",")
            semesters = semesters.split(",")
            tags = tags.split(",")
        except Exception as e:
            st.error(f"Error fetching metadata for {selected_file}: {e}")
            return
        file_name = file_name or selected_file.replace(".pdf", "")
        new_name = st.text_input("File Name", value=file_name, key="edit_name")
        departments = st.multiselect(
            "Department(s)",
            options=["All"] + DEPARTMENTS,
            default=departments,
            key="edit_dept"
        )
        semesters = st.multiselect(
            "Semester(s)",
            options=["All"] + SEMESTERS,
            default=semesters,
            key="edit_sem"
        )
        tags = st.multiselect(
            "Tags",
            options=PREDEFINED_TAGS,
            default=tags,
            key="edit_tags"
        )
        if st.button("Save Changes"):
            try:
                save_metadata_csv(
                    new_name,
                    departments,
                    semesters,
                    tags
                )
                st.success("Metadata updated successfully!")
                st.session_state.edited_files_session.append(selected_file)
            except Exception as e:
                st.error(f"Error updating metadata: {e}")
        if st.button("Delete File"):
            try:
                os.remove(os.path.join(DOCUMENTS_DIR, selected_file))
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                st.success(f"File {selected_file} and its metadata deleted successfully!")
                st.session_state.deleted_files_session.append(selected_file)
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting file: {e}")
    else:
        st.warning("No file selected.")

def update_knowledge_base_page():
    st.subheader("📚 Updating Knowledge Base")
    uploaded = st.session_state.get("uploaded_files_session", [])
    edited = st.session_state.get("edited_files_session", [])
    deleted = st.session_state.get("deleted_files_session", [])
    st.write(f"**New Uploads**: {uploaded}")
    st.write(f"**Edited Metadata**: {edited}")
    st.write(f"**Deleted Files**: {deleted}")
    progress_bar = st.progress(0)
    if st.button("Run Update Now", key="run_update_btn"):
    try:
        import time
        with st.spinner("Updating knowledge base..."):
            progress_bar.progress(10)
        response = requests.post(
            "http://localhost:8000/update_knowledge_base",
            json={
                "new_files": uploaded,
                "updated_files": edited,
                "deleted_files": deleted
            }
        )
        progress_bar.progress(90)
        time.sleep(0.2)
                
        if response.status_code == 200:
            st.success("✅ Knowledge base updated successfully!")
            st.session_state.uploaded_files_session = []
            st.session_state.edited_files_session = []
            st.session_state.deleted_files_session = []
            progress_bar.progress(100)
        else:
            st.error(f"Error updating knowledge base: {response.text}")
            progress_bar.progress(0)
    except Exception as e:
        st.error(f"Error connecting to FastAPI server: {e}")
        progress_bar.progress(0)

if st.session_state.page == "Home":
    homepage()
elif st.session_state.page == "Upload Files":
    upload_page()
elif st.session_state.page == "Edit Existing Files":
    edit_page()
elif st.session_state.page == "Update Knowledge Base":
    update_knowledge_base_page()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Update Knowledge Base"):
    st.session_state.page = "Update Knowledge Base"