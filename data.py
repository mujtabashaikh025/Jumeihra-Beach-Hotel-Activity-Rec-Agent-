import pandas as pd
import datetime
import random

# ==========================================
# 1. DEFINE THE ACTIVITY POOL (The "Menu")
# ==========================================
# We define templates for activities that happen on specific days
activity_pool = [
    # DAILY / FREQUENT
    {"Name": "Sunrise Yoga", "Type": "Activity", "Tags": "Wellness", "Time": "07:00", "Min_Age": 16, "Days": [0, 1, 2, 3, 4, 5, 6], "Price": "50 AED"}, # Every day
    {"Name": "Aqua Aerobics", "Type": "Activity", "Tags": "Wellness, Pool", "Time": "09:00", "Min_Age": 12, "Days": [1, 3, 5], "Price": "Free"}, # Mon, Wed, Fri
    {"Name": "Happy Hour Mixer", "Type": "Event", "Tags": "Social, Alcohol", "Time": "17:00", "Min_Age": 18, "Days": [0, 1, 2, 3, 4], "Price": "Pay as you go"}, # Weekdays

    # WEEKEND SPECIALS
    {"Name": "Rooftop DJ Party", "Type": "Event", "Tags": "Nightlife, Music", "Time": "21:00", "Min_Age": 18, "Days": [4, 5], "Price": "100 AED (Entry)"}, # Fri, Sat
    {"Name": "Sunday Grand Brunch", "Type": "Event", "Tags": "Food, Family", "Time": "11:00", "Min_Age": 0, "Days": [6], "Price": "250 AED"}, # Sunday only
    {"Name": "Kids Treasure Hunt", "Type": "Activity", "Tags": "Family, Kids", "Time": "10:00", "Min_Age": 4, "Days": [5, 6], "Price": "Free"}, # Sat, Sun

    # UNIQUE EXPERIENCES (Specific Days)
    {"Name": "Cooking Masterclass", "Type": "Activity", "Tags": "Food, Culture", "Time": "14:00", "Min_Age": 12, "Days": [2], "Price": "150 AED"}, # Wednesday
    {"Name": "Whiskey Tasting", "Type": "Event", "Tags": "Luxury, Alcohol", "Time": "20:00", "Min_Age": 21, "Days": [4], "Price": "300 AED"}, # Friday
    {"Name": "Local History Tour", "Type": "Activity", "Tags": "Sightseeing", "Time": "09:00", "Min_Age": 10, "Days": [1, 3], "Price": "80 AED"}, # Tue, Thu
    {"Name": "Scuba Diving Basics", "Type": "Package", "Tags": "Adventure", "Time": "08:00", "Min_Age": 15, "Days": [5], "Price": "400 AED"}, # Saturday
    {"Name": "Cinema Under Stars", "Type": "Event", "Tags": "Relax, Family", "Time": "20:00", "Min_Age": 0, "Days": [0, 3], "Price": "Free"}, # Mon, Thu
    {"Name": "Ladies Spa Afternoon", "Type": "Service", "Tags": "Wellness, Spa", "Time": "13:00", "Min_Age": 18, "Target_Gender": "Female", "Days": [1], "Price": "200 AED"}, # Tuesday
]

# ==========================================
# 2. GENERATE THE 30-DAY SCHEDULE
# ==========================================
schedule_rows = []
start_date = datetime.date.today()

for day_offset in range(30):
    current_date = start_date + datetime.timedelta(days=day_offset)
    day_of_week = current_date.weekday() # 0=Monday, 6=Sunday
    
    # Check every activity in the pool
    for activity in activity_pool:
        # If the activity is scheduled for this day of the week
        if day_of_week in activity["Days"]:
            schedule_rows.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Day_Name": current_date.strftime("%A"),
                "Activity_Name": activity["Name"],
                "Type": activity["Type"],
                "Start_Time": activity["Time"],
                "Tags": activity["Tags"],
                "Price": activity["Price"],
                "Min_Age": activity["Min_Age"],
                "Target_Gender": activity.get("Target_Gender", "Any")
            })

# Create DataFrame
df_30_day_schedule = pd.DataFrame(schedule_rows)
df_schedule = df_30_day_schedule

# ==========================================
# TABLE 2: GUEST DATA (10 Records)
# ==========================================
guest_data = {
    "Guest_ID": ["G-101", "G-102", "G-103", "G-104", "G-105", "G-106", "G-107", "G-108", "G-109", "G-110"],
    "Last_Name": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"],
    "Primary_Age": [29, 34, 22, 60, 45, 72, 31, 26, 40, 50],
    "Primary_Gender": ["Male", "Female", "Male", "Male", "Female", "Female", "Male", "Female", "Male", "Female"],
    "Room_Number": ["305", "402", "101", "500", "205", "105", "601", "303", "404", "505"],
    "Duration_Stay": [2, 5, 1, 7, 3, 10, 4, 2, 6, 3],
    "Group_Type": ["Individual", "Family", "Individual", "Couple", "Family", "Couple", "Couple", "Friends", "Family", "Individual"],
    
    # Nested Data for Families/Groups
    "Family_Members": [
        [], # G-101 (Solo Business)
        
        [{"Age": 8, "Gender": "Female", "Role": "Child"}, {"Age": 36, "Gender": "Male", "Role": "Spouse"}], # G-102 (Family with Kid)
        
        [], # G-103 (Solo Backpacker)
        
        [{"Age": 58, "Gender": "Female", "Role": "Spouse"}], # G-104 (Senior Couple)
        
        [{"Age": 15, "Gender": "Male", "Role": "Teen"}, {"Age": 17, "Gender": "Female", "Role": "Teen"}], # G-105 (Family with Teens)
        
        [{"Age": 75, "Gender": "Male", "Role": "Spouse"}], # G-106 (Elderly Couple)
        
        [{"Age": 29, "Gender": "Female", "Role": "Spouse"}], # G-107 (Young Couple/Honeymooners)
        
        [{"Age": 27, "Gender": "Female", "Role": "Friend"}], # G-108 (Girlfriends Trip)
        
        [{"Age": 10, "Gender": "Male", "Role": "Child"}, {"Age": 12, "Gender": "Female", "Role": "Child"}], # G-109 (Family with 2 Kids)
        

        
        [] # G-110 (Solo Traveler)
    ]
}

# ==========================================
# 2.1 ADD CHECK-IN / CHECK-OUT (Dynamic)
# ==========================================
# We simulate check-in based on today's date so data is always relevant
base_time = datetime.datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
check_ins = []
check_outs = []

# Mock arrival offsets relative to today (0 means checking in today, -1 means yesterday)
# This ensures some guests are partially through their stay
arrival_offsets = [0, -1, 0, -2, -1, -3, 0, 0, 1, -1]

for i, duration in enumerate(guest_data["Duration_Stay"]):
    # Check In
    check_in_dt = base_time + datetime.timedelta(days=arrival_offsets[i])
    check_ins.append(check_in_dt.strftime("%Y-%m-%d %H:%M"))
    
    # Check Out
    check_out_dt = check_in_dt + datetime.timedelta(days=duration)
    # Assume 11 AM check out
    check_out_dt = check_out_dt.replace(hour=11, minute=0)
    check_outs.append(check_out_dt.strftime("%Y-%m-%d %H:%M"))

guest_data["Check_In"] = check_ins
guest_data["Check_Out"] = check_outs


df_guests = pd.DataFrame(guest_data)
df_guests.to_csv("guest_data.csv", index=False)
df_schedule.to_csv("hotel_schedule.csv", index=False)
# print(df_guests)
# ==========================================
# 3. DISPLAY RESULTS
# ==========================================
# Show first 15 rows to verify it works
# print(f"Total Events Scheduled: {len(df_30_day_schedule)}")
# print(df_30_day_schedule.head(15).to_string(index=False))

# # Optional: Save to CSV
# df_30_day_schedule.to_csv("hotel_30_day_schedule.csv", index=False)