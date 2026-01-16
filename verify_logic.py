import pandas as pd
from chat_app import get_guest_schedule, load_data

# Mock data loading to avoid Streamlit cache issues in script
def test_schedule_logic():
    print("Testing get_guest_schedule logic...")
    
    # Load actual data (using the function from chat_app might trigger st dependencies, 
    # so we'll just read csv directly for this test context or mock it if needed. 
    # But chat_app imports streamlit at top level, so running this script might need streamlit installed.
    # We will try to rely on the fact that we can import from chat_app if we mock streamlit first OR 
    # just reimplement the logic here for confirmation if importing fails.
    # Let's try importing first, but we need to mock streamlit since it's used in chat_app global scope.
    pass

# Actually it's safer to copy the logic into this script to verify it independently 
# without triggering Streamlit's "Warning: to view this Streamlit app..." or errors.

# 1. Load Data
try:
    df_schedule = pd.read_csv("hotel_schedule.csv")
    print(f"Loaded schedule with {len(df_schedule)} rows.")
except Exception as e:
    print(f"Failed to load schedule: {e}")
    exit()

def get_guest_schedule_isolated(check_in, check_out, df_schedule):
    """Filter hotel schedule for the guest's stay (Isolated version)."""
    try:
        # Convert check-in/out to datetime objects
        cin_dt = pd.to_datetime(check_in)
        cout_dt = pd.to_datetime(check_out)
        
        # Create a full datetime column for the schedule
        # Combine Date and Start_Time
        df_schedule = df_schedule.copy()
        df_schedule['Activity_DateTime'] = pd.to_datetime(df_schedule['Date'].astype(str) + ' ' + df_schedule['Start_Time'].astype(str))
        
        # Filter based on exact timing
        # Activity must start AFTER check-in and BEFORE check-out
        mask = (df_schedule['Activity_DateTime'] >= cin_dt) & (df_schedule['Activity_DateTime'] <= cout_dt)
        stay_schedule = df_schedule.loc[mask].drop(columns=['Activity_DateTime'])
        
        return stay_schedule
    except Exception as e:
        return f"Error processing schedule: {e}"

# Test Case 1: Check-in at 2 PM (14:00). Should exclude 7 AM Yoga on arrival day.
check_in = "2026-01-13 14:00:00"
check_out = "2026-01-15 11:00:00"

print(f"\n--- Test Case 1 ---")
print(f"Check-in: {check_in}")
print(f"Check-out: {check_out}")

activities = get_guest_schedule_isolated(check_in, check_out, df_schedule)

if isinstance(activities, str):
    print(activities)
else:
    print(f"Found {len(activities)} activities.")
    # Check for arrival day activities
    arrival_date = pd.to_datetime(check_in).date()
    # Check if there are any activities on arrival day BEFORE 14:00
    for _, row in activities.iterrows():
        act_dt = pd.to_datetime(row['Date'] + ' ' + row['Start_Time'])
        print(f" - {row['Activity_Name']} at {act_dt}")
        if act_dt < pd.to_datetime(check_in):
            print("   [FAIL] Found activity before check-in!")
        if act_dt > pd.to_datetime(check_out):
            print("   [FAIL] Found activity after check-out!")

print("\n--- Test Finished ---")
