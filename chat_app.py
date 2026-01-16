import streamlit as st
import pandas as pd
import os
import datetime
import json
import re
from google import genai
from dotenv import load_dotenv
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(page_title="Hotel Concierge", page_icon="🏨")

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)
else:
    st.error("GEMINI_API_KEY not found. Please check your .env file.")

# ==========================================
# DATA LOADING
# ==========================================
@st.cache_data
def load_data():
    try:
        # Load Guests
        guests = pd.read_csv("guest_data.csv")
        # Ensure ID is string
        guests["Guest_ID"] = guests["Guest_ID"].astype(str)
        
        # Load Schedule
        schedule = pd.read_csv("hotel_schedule.csv")
        return guests, schedule
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_guests, df_schedule = load_data()

# ==========================================
# SESSION STATE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_stage" not in st.session_state:
    st.session_state.chat_stage = "LOGIN"  # LOGIN, GREETING, OFFER_HELP, PREFERENCE, RESULT

if "guest_info" not in st.session_state:
    st.session_state.guest_info = None

if "booking_request" not in st.session_state:
    st.session_state.booking_request = None



# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_guest_schedule(check_in, check_out):
    """Filter hotel schedule for the guest's stay."""
    try:
        # Convert check-in/out to datetime objects
        cin_dt = pd.to_datetime(check_in)
        cout_dt = pd.to_datetime(check_out)
        
        # Create a full datetime column for the schedule
        # Combine Date and Start_Time
        df_schedule['Activity_DateTime'] = pd.to_datetime(df_schedule['Date'].astype(str) + ' ' + df_schedule['Start_Time'].astype(str))
        
        # Filter based on exact timing
        # Activity must start AFTER check-in and BEFORE check-out
        mask = (df_schedule['Activity_DateTime'] >= cin_dt) & (df_schedule['Activity_DateTime'] <= cout_dt)
        stay_schedule = df_schedule.loc[mask].drop(columns=['Activity_DateTime'])
        
        return stay_schedule.to_dict('records')
    except Exception as e:
        return f"Error processing schedule: {e}"

def generate_ai_response(user_input, context_prompt=""):
    """Call Gemini to generate response."""
    if not client:
        return "I'm sorry, my language core is offline (API Key missing)."
    
    try:
        full_prompt = f"{context_prompt}\n\nUser Message: {user_input}"
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"I apologize, I'm having trouble connecting right now. ({e})"

def parse_json_response(text):
    """Extract and parse JSON from LLM response."""
    try:
        # Clean up markdown code blocks if present
        cleaned_text = re.sub(r'```json\s*|\s*```', '', text).strip()
        return json.loads(cleaned_text)
    except Exception:
        return None

def get_activity_image(activity_name):
    """Find local image for activity."""
    image_dir = "activities"
    if not os.path.exists(image_dir):
        return None
    
    # Normalize activity name
    target = activity_name.lower().replace(" ", "")
    
    # Special mappings if needed
    if "yoga" in target: return os.path.join(image_dir, "yoga.png")
    if "happyhour" in target: return os.path.join(image_dir, "happyhour.png")
    
    for filename in os.listdir(image_dir):
        if filename.startswith("."): continue # Skip hidden files
        
        # Normalize filename (remove extension)
        base_name = os.path.splitext(filename)[0].lower().replace(" ", "")
        
        # Check for match
        if base_name in target or target in base_name:
             return os.path.join(image_dir, filename)
             
    return None

def send_booking_confirmation_email(guest_info, activity, ref_number):
    """Send booking details to admin email."""
    # Force reload env to pick up changes without restarting server entirely if possible
    load_dotenv(override=True)
    
    sender_email = os.getenv("SMTP_EMAIL")
    password_raw = os.getenv("SMTP_PASSWORD", "")
    sender_password = password_raw.replace(" ", "") # Remove spaces from App Password
    
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    receiver_email = "mujtabashaikh025@gmail.com"

    # Construct Message
    subject = f"New Booking: {guest_info.get('Last_Name')} - Room {guest_info.get('Room_Number')}"
    
    body = f"""
    New Booking Confirmed
    =====================
    
    GUEST DETAILS:
    - Last Name:   {guest_info.get('Last_Name')}
    - Room Number: {guest_info.get('Room_Number')}
    
    ACTIVITY DETAILS:
    - Activity:    {activity.get('activity_name')}
    - Date:        {activity.get('date')}
    - Day:         {activity.get('day', 'N/A')}
    - Time:        {activity.get('time')}
    
    Reference Ref: {ref_number}
    """

    if not sender_email or not sender_password:
        return False, "SMTP Credentials missing (simulated)"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

def render_activity_cards(activities):
    """Render activities using native Streamlit containers."""
    for act in activities:
        # Fallbacks
        title = act.get('activity_name', 'Activity')
        
        # Try local image first
        local_img = get_activity_image(title)
        if local_img:
            img_url = local_img
        else:
            img_url = act.get('image', 'https://via.placeholder.com/800x600?text=No+Image')
            
        date = act.get('date', '')
        time = act.get('time', '')
        price = act.get('price', '')
        desc = act.get('description', '')

        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(img_url, use_container_width=True)
            
            with col2:
                st.subheader(title)
                st.caption(f"📅 {date} | ⏰ {time}")
                st.markdown(f"**{price}**")
                st.write(desc)
                
                # Unique key for the button is critical
                # We use a combination of fields to ensure uniqueness
                btn_key = f"book_{title}_{date}_{time}".replace(" ", "_")
                if st.button("Book Now", key=btn_key):
                    st.session_state.booking_request = act
                    st.rerun()

# ==========================================
# UI & LOGIC
# ==========================================

# Display Logo Image (Centered)
col1, col2, col3 = st.columns([3, 1, 3])
with col2:
    try:
        st.image("logo.png.avif", use_container_width=True)
    except Exception:
        pass # Fallback if image fails

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');

.logo-container {
    text-align: center;
    padding: 1rem 0;
    border-bottom: 2px solid #C5A059;
    margin-bottom: 2rem;
}
.logo-text {
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    font-weight: 700;
    color: #C5A059;
    margin-bottom: 0.2rem;
    text-transform: uppercase;
    letter-spacing: 2px;
}
.logo-subtitle {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    color: #ECCFA1;
    font-style: italic;
    letter-spacing: 1px;
}
</style>
<div class="logo-container">
    <div class="logo-text">Jumeirah Beach Hotel</div>
    <div class="logo-subtitle">Hotel Activity Concierge</div>
</div>
""", unsafe_allow_html=True)

# --- STEP 1: LOGIN (Simulated) ---
# --- STEP 1: LOGIN (Simulated) ---
# Automatically select a random guest for the demo
if st.session_state.chat_stage == "LOGIN":
    # Pick a random guest
    if not df_guests.empty:
        random_guest = df_guests.sample(n=1).iloc[0]
        st.session_state.guest_info = random_guest.to_dict()
        st.session_state.chat_stage = "GREETING"
        st.rerun()
    else:
        st.error("No guest data found.")

# --- CHAT INTERFACE ---
else:
    # Handle Booking Request (processed before rendering to update history immediately)
    if st.session_state.booking_request:
        act = st.session_state.booking_request
        
        # User Message
        user_msg = f"I would like to book **{act.get('activity_name')}** for {act.get('price')}."
        st.session_state.messages.append({"role": "user", "content": user_msg})
        
        # Check if Free
        price_str = str(act.get('price', '')).lower().strip()
        is_free = (price_str == "free")
        
        if is_free:
            # Auto-confirm
            ref_num = f"{random.randint(100000, 999999)}"
            
            # Send Email
            success, status = send_booking_confirmation_email(st.session_state.guest_info, act, ref_num)
            
            # Add Success Message directly
            success_msg = (
                f"✅ **Booking Confirmed!**\n\n"
                f"You have been booked for **{act.get('activity_name')}**.\n"
                f"Reference Number: `{ref_num}`\n\n"
                f"We have sent a confirmation details to the front desk."
            )
            st.session_state.messages.append({"role": "assistant", "content": success_msg})
            
            if success:
                 st.toast("Confirmation email sent!", icon="📧")
            else:
                 print(f"Email failed: {status}")
                 st.error(f"Email Failed: {status}")

            # Clear request
            st.session_state.booking_request = None
            st.rerun()

        else:
            # Add Payment Request Message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": act,
                "type": "payment_request",
                "paid": False
            })
            
            # Clear request
            st.session_state.booking_request = None
            st.rerun()

    # Display Chat History
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg.get("type") == "json_cards":
                render_activity_cards(msg["content"])
            elif msg.get("type") == "payment_request":
                act = msg["content"]
                if msg.get("paid"):
                    st.success(f"Payment Successful! Booking confirmed for {act.get('activity_name')}.")
                    ref_num = msg.get("ref_num", "N/A") # Retrieve stored ref if available
                    st.caption(f"Ref: {ref_num}")
                else:
                    st.write(f"Excellent choice! Please confirm your booking for **{act.get('activity_name')}**.")
                    if st.button("Tap to Pay & Confirm 💳", key=f"pay_btn_{i}"):
                        msg["paid"] = True
                        
                        # Generate Reference
                        ref_num = f"{random.randint(100000, 999999)}"
                        msg["ref_num"] = ref_num
                        
                        # Send Email
                        success, status = send_booking_confirmation_email(st.session_state.guest_info, act, ref_num)
                        
                        if success:
                            st.toast("Confirmation email sent!", icon="📧")
                        else:
                            # Log failure
                            print(f"Email failed: {status}") 
                            st.error(f"Email Failed: {status}") # Show error to user for debugging
                            if "simulated" in status:
                                st.info("Check your .env file for SMTP credentials.")

                        st.rerun()
            else:
                st.markdown(msg["content"])

    # Initial Greeting Trigger (Auto-run once)
    if st.session_state.chat_stage == "GREETING" and not st.session_state.messages:
        last_name = st.session_state.guest_info['Last_Name']
        greeting = (
            f"Hi, {last_name}. It is a pleasure to welcome you to Jumeirah Beach Hotel. "
            "I am Sarah, your dedicated virtual concierge. May I assist you in booking any "
            "leisure activities or experiences to enhance your stay?"
        )
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.chat_stage = "OFFER_HELP"
        st.rerun()

    # Chat Input
    if user_input := st.chat_input("Type your response here..."):
        # 1. Add User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Process Assistant Response
        response_text = ""
        is_json_response = False
        parsed_activities = []
        
        # STATE: OFFER_HELP -> PREFERENCE
        if st.session_state.chat_stage == "OFFER_HELP":
            # Simple check for Yes/No
            # In a real app, we'd use LLM to classify intent, but simple keyword matching works for "Yes/No"
            if any(word in user_input.lower() for word in ['no', 'nope', 'not now']):
                response_text = "Certainly. Please feel free to reach out if you change your mind. Enjoy your stay!"
                st.session_state.chat_stage = "ENDED"
            else:
                response_text = (
                    "Do you want me to personalize any experience for you, or shall I "
                    "give you a list of activities according to your schedule?"
                )
                st.session_state.chat_stage = "PREFERENCE"

        # STATE: PREFERENCE -> PERSONALIZE or LIST
        elif st.session_state.chat_stage == "PREFERENCE":
            if "personal" in user_input.lower():
                response_text = (
                    "I'd love to curate something special for you. Could you tell me a bit more about what you're in the mood for? "
                    "For example: Are you looking for relaxation, adventure, family fun, or dining experiences?"
                )
                st.session_state.chat_stage = "PERSONALIZE_Q_AND_A"
            else:
                # Default to List
                # Generate List
                check_in = st.session_state.guest_info['Check_In']
                check_out = st.session_state.guest_info['Check_Out']
                stay_activities = get_guest_schedule(check_in, check_out)
                
                # Context for Gemini to format the list
                prompt = (
                    f"Act as Sarah, the hotel concierge.\n"
                    f"Guest Name: {st.session_state.guest_info['Last_Name']}\n"
                    f"Stay: {check_in} to {check_out}\n"
                    f"Activities Available:\n{stay_activities}\n\n"
                    "Request: Provide the complete list of activities for their stay schedule.\n"
                    "Requirements:\n"
                    "1. Return ONLY a JSON array of objects. Do not include any markdown formatting or extra text.\n"
                    "2. Each object must have keys: 'day', 'date', 'time', 'activity_name', 'price', 'description'.\n"
                    "3. Do NOT generate an image URL. Images are handled locally.\n"
                )
                
                with st.spinner("Retrieving your schedule..."):
                    raw_response = generate_ai_response(user_input, prompt)
                    parsed_json = parse_json_response(raw_response)
                    
                    if parsed_json:
                        is_json_response = True
                        parsed_activities = parsed_json
                        response_text = "Here are the activities available during your stay:"
                    else:
                        response_text = raw_response # Fallback to text if JSON fails

                st.session_state.chat_stage = "RESULT"

        # STATE: PERSONALIZE_Q_AND_A -> RESULT
        elif st.session_state.chat_stage == "PERSONALIZE_Q_AND_A":
             # This block handles the "Answer" to the personalization question
             # We assume the user just answered "I like diving" or similar.
             
             check_in = st.session_state.guest_info['Check_In']
             check_out = st.session_state.guest_info['Check_Out']
             guest_profile = st.session_state.guest_info
             stay_activities = get_guest_schedule(check_in, check_out)
             
             prompt = (
                f"Act as Sarah, the dedicated and knowledgeable hotel concierge at Jumeirah Beach Hotel.\n"
                f"Guest Profile: {guest_profile}\n"
                f"Activities Available:\n{stay_activities}\n"
                f"Context: The guest asked for personalized recommendations and just replied: '{user_input}'\n\n"
                "Task: Carefully analyze the guest's profile (especially Age, Gender, and Family Members) and their request. Select the best matching activities from the available list.\n"
                "Requirements:\n"
                "1. Return ONLY a JSON array of objects. Do not include any markdown formatting or extra text.\n"
                "2. Each object must have keys: 'day', 'date', 'time', 'activity_name', 'price', 'description'.\n"
                "3. Do NOT generate an image URL. Images are handled locally.\n"
                "4. STRICTLY MATCH INTERESTS: Check the 'Tags' column in the activities. If the user asks for 'relax', look for 'Wellness', 'Spa', 'Relax'. If 'party', look for 'Social', 'Alcohol', 'Nightlife'.\n"
                "5. STRICTLY ENFORCE CONSTRAINTS: Check 'Min_Age' and 'Target_Gender' against the Guest Profile. Do not recommend activities the guest (or their children) cannot attend.\n"
                "6. If the user mentions a specific day or time, prioritize those.\n"
            )
             
             with st.spinner("Curating your personalized itinerary..."):
                 raw_response = generate_ai_response(user_input, prompt)
                 parsed_json = parse_json_response(raw_response)
                 
                 if parsed_json:
                     is_json_response = True
                     parsed_activities = parsed_json
                     response_text = "Here are some personalized recommendations for you:"
                 else:
                     response_text = raw_response

             st.session_state.chat_stage = "RESULT" # OR Keep in Q_AND_A if we want multi-turn

        # STATE: RESULT (or fallback)
        else:
             # Just continue conversation or handle additional questions
             # Pass history context if possible in a real app, keeping it simple here
             response_text = generate_ai_response(user_input, 
                "Act as Sarah, hotel concierge. The user is asking a follow-up question. Be helpful and brief."
             )

        # 3. Display Assistant Response
        if response_text:
            if is_json_response:
                # Append text intro
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                
                # Append JSON cards for history
                st.session_state.messages.append({"role": "assistant", "content": parsed_activities, "type": "json_cards"})
                with st.chat_message("assistant"):
                    render_activity_cards(parsed_activities)
            else:
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                with st.chat_message("assistant"):
                    st.markdown(response_text)