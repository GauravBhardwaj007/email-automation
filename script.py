import smtplib
import time
import pytz
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import streamlit as st
import os
from dotenv import load_dotenv
import psutil  # Import psutil to fetch memory, CPU, and storage usage

# Load environment variables from .env file
load_dotenv()

# Get email credentials from Streamlit secrets
EMAIL_USER = st.secrets["email"]["EMAIL_USER"]
EMAIL_PASS = st.secrets["email"]["EMAIL_PASS"]
LOGIN_USERNAME = st.secrets["login"]["LOGIN_USERNAME"]
LOGIN_PASSWORD = st.secrets["login"]["LOGIN_PASSWORD"]

# Ensure credentials are loaded
if not EMAIL_USER or not EMAIL_PASS:
    st.error("Invalid credentials for sender")
    exit(1)

if not LOGIN_USERNAME or not LOGIN_PASSWORD:
    st.error("Invalid credentials")
    exit(1)

# Email sending settings
SERVER = 'smtp.gmail.com'
PORT = 587

# Function to check if it's time to send the email
def check_time_to_send(desired_time, desired_date):
    tz = pytz.timezone("Asia/Kolkata")  # Indian Standard Time
    current_time = datetime.now(tz).strftime('%H:%M')  # Get current time in HH:MM format (IST)
    current_date = datetime.now(tz).strftime('%Y-%m-%d')  # Get current date in YYYY-MM-DD format (IST)
    return current_time == desired_time and current_date == desired_date  # Compare current time and date with desired

# Function to get current memory usage (RAM) in GB/MB
def get_memory_usage():
    memory = psutil.virtual_memory()
    total_memory = memory.total / (1024 ** 3)  # Total memory in GB
    used_memory = memory.used / (1024 ** 3)   # Used memory in GB
    return total_memory, used_memory  # Only return used memory and total memory

# Function to get current CPU usage in real numbers (e.g., total usage)
def get_cpu_usage():
    total_cpu = psutil.cpu_percent(interval=1)  # Total CPU usage over 1 second
    cpu_cores = psutil.cpu_percent(interval=1, percpu=True)  # Usage per CPU core
    return total_cpu, cpu_cores

# Function to get current storage usage in GB for the specific app's directory
def get_app_storage_usage():
    app_directory = os.getcwd()  # Current working directory where Streamlit is running
    total_size = 0

    # Walk through all files in the app's directory and calculate the total size
    for dirpath, dirnames, filenames in os.walk(app_directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)  # Add file size in bytes

    # Convert the size to MB (not GB)
    total_size_mb = total_size / (1024 ** 2)  # Convert bytes to MB
    return total_size_mb

# Function to get the memory usage of the current Streamlit process (the app's process)
def get_streamlit_memory_usage():
    process = psutil.Process(os.getpid())  # Get the current process (Streamlit)
    memory_info = process.memory_info()  # Memory info in bytes
    used_memory = memory_info.rss / (1024 ** 2)  # Convert bytes to MB
    return used_memory

# Streamlit UI - Login Page
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown('<h1 style="text-align: center;">GreenBhumi Volunteers</h1>', unsafe_allow_html=True)

    # Create columns for login form layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        username_input = st.text_input("Username")
    with col2:
        password_input = st.text_input("Password", type="password")
    
    login_button = st.button("Login", use_container_width=True)  # Login button placed below the inputs

    if login_button:
        if username_input == LOGIN_USERNAME and password_input == LOGIN_PASSWORD:
            st.session_state.logged_in = True  # Set session state to indicate the user is logged in
            st.success("Logged in successfully!")
            st.rerun()  # Rerun to update the interface after login
        else:
            st.error("Invalid username or password")

# Show the email scheduling functionality if logged in
if 'logged_in' in st.session_state and st.session_state.logged_in:
    st.markdown('<h1 style="text-align: center;">Quiz reminder mail for GreenBhumi</h1>', unsafe_allow_html=True)

    # Real-time system resource usage placeholders
    memory_placeholder = st.empty()  # Placeholder for memory usage
    cpu_placeholder = st.empty()  # Placeholder for CPU usage
    storage_placeholder = st.empty()  # Placeholder for storage usage

    # Function to display the resource usage every 2 seconds without blocking the UI
    def update_resource_usage():
        total_memory, used_memory = get_memory_usage()
        total_cpu, cpu_cores = get_cpu_usage()
        app_storage_used = get_app_storage_usage()  # Get the used space for the Streamlit app's directory
        streamlit_memory = get_streamlit_memory_usage()  # Get Streamlit's memory usage

        # Update the metrics
        memory_placeholder.metric("Total Memory", f"{total_memory:.2f} GB")
        memory_placeholder.metric("USING RAM (Streamlit)", f"{streamlit_memory:.2f} MB")  # Display used RAM in MB
        
        cpu_placeholder.metric("Total CPU Usage", f"{total_cpu}%")
        cpu_placeholder.write("CPU Core Usage:")
        for i, usage in enumerate(cpu_cores, start=1):
            cpu_placeholder.write(f"Core {i}: {usage}%")

        storage_placeholder.metric("Space Used by App", f"{app_storage_used:.2f} MB")  # Display space used by Streamlit app in MB

    # Updating the system resource usage
    update_resource_usage()

    # Initialize session state for recipients and scheduled emails if not already done
    if 'recipients' not in st.session_state:
        st.session_state.recipients = []
    if 'scheduled_emails' not in st.session_state:
        st.session_state.scheduled_emails = []

    # Form to input name and email manually
    st.subheader('Enter the recipient details')

    # Create a form to allow users to input names and emails
    with st.form(key='email_form'):
        # Create columns for name and email inputs
        col1, col2 = st.columns([2, 3])
        
        with col1:
            name_input = st.text_input("Enter recipient's name", key="name_input")
        with col2:
            email_input = st.text_input("Enter recipient's email address", key="email_input")

        submit_button = st.form_submit_button("Add Recipient", use_container_width=True)

        if submit_button:
            if name_input and email_input:
                if any(email_input == recipient[1] for recipient in st.session_state.recipients):
                    st.error(f"{email_input} is already in the recipient list.")
                else:
                    # Add recipient without any status
                    st.session_state.recipients.append((name_input, email_input))
                    st.success(f"Added {name_input} ({email_input}) to the recipient list.")
                    name_input = ""
                    email_input = ""

    # Display the list of added recipients in a dropdown with option to remove
    if st.session_state.recipients:
        st.write("### Recipient List")
        
        # Create dropdown options from the recipients
        recipient_options = [f"{name} - {email}" for name, email in st.session_state.recipients]
        selected_recipient = st.selectbox("Select a recipient to remove", options=[""] + recipient_options)

        # Button to remove the selected recipient
        if selected_recipient and st.button("Remove Selected Recipient"):
            selected_recipient_index = recipient_options.index(selected_recipient) - 1  # Adjust for empty option
            removed_name, removed_email = st.session_state.recipients.pop(selected_recipient_index)
            st.success(f"Removed {removed_name} ({removed_email}) from the recipient list.")

    # Email subject and body inputs
    subject = st.text_input("Enter the subject of the email", "QUIZ REMINDER")
    body = st.text_area("Enter the email body", "It is your turn to update the quiz tomorrow :)")

    # Desired time to send the email (HH:MM format)
    desired_time = st.text_input("Enter the time to send emails (HH:MM format)", "21:00")
    # Desired date to send the email (YYYY-MM-DD format)
    desired_date = st.date_input("Enter the date to send emails (YYYY-MM-DD)", datetime.today())

    # Submit button to send emails
    if st.button("Send Emails", use_container_width=True):
        if not st.session_state.recipients:
            st.warning("Please add at least one recipient before sending.")
        else:
            try:
                server = smtplib.SMTP(SERVER, PORT)
                server.set_debuglevel(1)
                server.ehlo()
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)

                # Create a list of emails to be sent after the button is clicked
                st.session_state.scheduled_emails = st.session_state.recipients.copy()
                st.session_state.recipients = []

                # Display waiting message
                st.write("Waiting to send emails at the scheduled time...")

                # Show the cancellation option immediately after scheduling emails
                st.write("### Cancel Scheduled Emails")
                scheduled_email_options = [f"{name} - {email}" for name, email in st.session_state.scheduled_emails]
                cancel_recipient = st.selectbox("Select a recipient to cancel", options=[""] + scheduled_email_options)

                # Button to cancel selected email
                if cancel_recipient:
                    if st.button("Cancel Selected Email"):
                        cancel_recipient_index = scheduled_email_options.index(cancel_recipient) - 1  # Adjust for empty option
                        canceled_name, canceled_email = st.session_state.scheduled_emails.pop(cancel_recipient_index)
                        st.success(f"Canceled email to {canceled_name} ({canceled_email}).")
                        st.rerun()  # Refresh the page to update the UI after canceling

                # Background email sending logic with lower sleep interval for testing
                for name, email in st.session_state.scheduled_emails:
                    while not check_time_to_send(desired_time, str(desired_date)):
                        time.sleep(10)  # Sleep for 10 seconds for testing

                    # Create the email
                    msg = MIMEMultipart()
                    msg['From'] = EMAIL_USER
                    msg['To'] = email
                    msg['Subject'] = subject

                    # Personalize email body
                    personalized_body = body.replace("{name}", name)
                    msg.attach(MIMEText(personalized_body, 'plain'))

                    # Send the email
                    server.sendmail(EMAIL_USER, email, msg.as_string())
                    st.write(f"Email sent to {name} ({email})")

                # Close the server after sending all emails
                server.quit()
                st.success("All emails sent successfully!")
                st.session_state.scheduled_emails = []  # Clear scheduled emails after sending
            except Exception as e:
                st.error(f"Error: {e}")
