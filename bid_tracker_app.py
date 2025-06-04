import streamlit as st
import pandas as pd
import random
import string
import datetime
from datetime import date
import json
import os

# Page configuration
st.set_page_config(
    page_title="Project Bid Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-submitted {
        background-color: #d4edda;
        color: #155724;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .status-draft {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .status-pending {
        background-color: #cce5ff;
        color: #004085;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .project-id {
        font-family: monospace;
        font-weight: bold;
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'projects' not in st.session_state:
    st.session_state.projects = []

# Authentication function
def authenticate(email, password):
    return email == "ermias@ketos.co" and password == "18221822"

# Generate project ID (first one is QB6TYKDHVWL9, then random)
def generate_project_id():
    # Check if this is the first project
    if not st.session_state.projects:
        return "QB6TYKDHVWL9"
    else:
        # Generate random ID for subsequent projects
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

# Load projects from file (simulate cloud storage)
def load_projects():
    try:
        if os.path.exists('projects.json'):
            with open('projects.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return []

# Save projects to file (simulate cloud storage)
def save_projects(projects):
    try:
        with open('projects.json', 'w') as f:
            json.dump(projects, f, indent=2, default=str)
    except:
        pass

# Login page
def login_page():
    st.markdown('<h1 class="main-header">🔐 Project Bid Tracker Login</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Please login to access your project dashboard")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button:
                if authenticate(email, password):
                    st.session_state.authenticated = True
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")

# Main dashboard
def main_dashboard():
    # Load projects on startup
    if not st.session_state.projects:
        st.session_state.projects = load_projects()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Project Bid Tracker Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio("Select Page", ["Dashboard", "Add New Project", "Project Details", "Analytics"])
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Add New Project":
        add_project_page()
    elif page == "Project Details":
        project_details_page()
    elif page == "Analytics":
        analytics_page()

def dashboard_page():
    st.markdown("## 📋 Project Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_projects = len(st.session_state.projects)
    submitted_projects = len([p for p in st.session_state.projects if p['status'] == 'Submitted'])
    draft_projects = len([p for p in st.session_state.projects if p['status'] == 'Draft'])
    pending_projects = len([p for p in st.session_state.projects if p['status'] == 'Pending Response'])
    
    with col1:
        st.metric("Total Projects", total_projects)
    with col2:
        st.metric("Submitted", submitted_projects)
    with col3:
        st.metric("Drafts", draft_projects)
    with col4:
        st.metric("Pending Response", pending_projects)
    
    st.markdown("---")
    
    # Projects table
    if st.session_state.projects:
        st.markdown("## 📊 All Projects")
        
        # Search and filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Search projects", placeholder="Search by title or ID...")
        with col2:
            status_filter = st.selectbox("Filter by Status", ["All", "Draft", "Submitted", "Pending Response"])
        
        # Filter projects
        filtered_projects = st.session_state.projects
        
        if search_term:
            filtered_projects = [p for p in filtered_projects 
                               if search_term.lower() in p['title'].lower() or search_term.lower() in p['id'].lower()]
        
        if status_filter != "All":
            filtered_projects = [p for p in filtered_projects if p['status'] == status_filter]
        
        # Display projects
        for project in filtered_projects:
            with st.expander(f"**{project['id']}** - {project['title']}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Description:** {project['description']}")
                    st.write(f"**Client:** {project['client']}")
                    if project['drive_link']:
                        st.markdown(f"**Google Drive:** [Open Document]({project['drive_link']})")
                
                with col2:
                    status_class = f"status-{project['status'].lower().replace(' ', '-')}"
                    st.markdown(f'<div class="{status_class}">{project["status"]}</div>', unsafe_allow_html=True)
                    st.write(f"**Created:** {project['created_date']}")
                
                with col3:
                    st.write(f"**Deadline:** {project['deadline']}")
                    st.write(f"**Value:** ${project['value']:,}")
    else:
        st.info("No projects found. Add your first project using the 'Add New Project' page!")

def add_project_page():
    st.markdown("## ➕ Add New Project")
    
    with st.form("add_project_form"):
        # Generate new project ID
        project_id = generate_project_id()
        st.markdown(f'**Project ID:** <span class="project-id">{project_id}</span>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Project Title*", placeholder="Enter project title")
            client = st.text_input("Client Name*", placeholder="Enter client name")
            description = st.text_area("Project Description", placeholder="Brief description of the project")
            drive_link = st.text_input("Google Drive Link", placeholder="https://drive.google.com/...")
            created_date = st.date_input("Created Date", value=date.today(), help="Select when this project was created")
        
        with col2:
            status = st.selectbox("Status", ["Draft", "Submitted", "Pending Response"])
            deadline = st.date_input("Deadline", min_value=date.today())
            value = st.number_input("Project Value ($)", min_value=0, step=1000)
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        submitted = st.form_submit_button("Add Project", use_container_width=True)
        
        if submitted:
            if title and client:
                new_project = {
                    'id': project_id,
                    'title': title,
                    'client': client,
                    'description': description,
                    'drive_link': drive_link,
                    'status': status,
                    'deadline': deadline,
                    'value': value,
                    'priority': priority,
                    'created_date': created_date,
                    'last_updated': datetime.datetime.now()
                }
                
                st.session_state.projects.append(new_project)
                save_projects(st.session_state.projects)
                
                st.success(f"✅ Project {project_id} added successfully!")
                st.balloons()
            else:
                st.error("Please fill in all required fields (marked with *)")

def project_details_page():
    st.markdown("## 📝 Project Details & Management")
    
    if not st.session_state.projects:
        st.info("No projects available. Add a project first!")
        return
    
    # Select project
    project_options = [f"{p['id']} - {p['title']}" for p in st.session_state.projects]
    selected_project = st.selectbox("Select Project", project_options)
    
    if selected_project:
        # Find the selected project
        project_id = selected_project.split(' - ')[0]
        project = next((p for p in st.session_state.projects if p['id'] == project_id), None)
        
        if project:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### {project['title']}")
                st.markdown(f"**Project ID:** `{project['id']}`")
                st.markdown(f"**Client:** {project['client']}")
                st.markdown(f"**Description:** {project['description']}")
                
                if project['drive_link']:
                    st.markdown(f"**Google Drive:** [Open Document]({project['drive_link']})")
            
            with col2:
                st.markdown("### Quick Actions")
                
                # Update status
                new_status = st.selectbox("Update Status", 
                                        ["Draft", "Submitted", "Pending Response"], 
                                        index=["Draft", "Submitted", "Pending Response"].index(project['status']))
                
                if st.button("Update Status"):
                    project['status'] = new_status
                    project['last_updated'] = datetime.datetime.now()
                    save_projects(st.session_state.projects)
                    st.success("Status updated!")
                    st.rerun()
                
                # Delete project
                if st.button("🗑️ Delete Project", type="secondary"):
                    st.session_state.projects = [p for p in st.session_state.projects if p['id'] != project_id]
                    save_projects(st.session_state.projects)
                    st.success("Project deleted!")
                    st.rerun()
            
            # Project timeline
            st.markdown("---")
            st.markdown("### 📅 Project Timeline")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Created", str(project['created_date']))
            with col2:
                st.metric("Deadline", str(project['deadline']))
            with col3:
                # Handle date conversion for days remaining calculation
                if isinstance(project['deadline'], str):
                    deadline_date = datetime.datetime.strptime(project['deadline'], '%Y-%m-%d').date()
                else:
                    deadline_date = project['deadline']
                days_remaining = (deadline_date - date.today()).days
                st.metric("Days Remaining", days_remaining)

def analytics_page():
    st.markdown("## 📈 Analytics & Insights")
    
    if not st.session_state.projects:
        st.info("No projects available for analytics. Add some projects first!")
        return
    
    # Status distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Project Status Distribution")
        status_counts = {}
        for project in st.session_state.projects:
            status = project['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            df_status = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
            st.bar_chart(df_status.set_index('Status'))
    
    with col2:
        st.markdown("### 💰 Total Project Value")
        total_value = sum(p['value'] for p in st.session_state.projects)
        st.metric("Total Portfolio Value", f"${total_value:,}")
        
        # Value by status
        value_by_status = {}
        for project in st.session_state.projects:
            status = project['status']
            value_by_status[status] = value_by_status.get(status, 0) + project['value']
        
        st.markdown("**Value by Status:**")
        for status, value in value_by_status.items():
            st.write(f"• {status}: ${value:,}")
    
    # Recent activity
    st.markdown("---")
    st.markdown("### 🕐 Recent Projects")
    
    # Sort projects by creation date
    recent_projects = sorted(st.session_state.projects, 
                           key=lambda x: x['created_date'], 
                           reverse=True)[:5]
    
    for project in recent_projects:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{project['title']}**")
        with col2:
            st.write(f"*{project['status']}*")
        with col3:
            st.write(f"${project['value']:,}")

# Main app logic
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
