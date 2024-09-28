import streamlit as st
import pandas as pd
from pathlib import Path

# Function to load and process the Excel data
@st.cache
def load_data(file_path):
    df = pd.read_excel(file_path)
    df = preprocess_dataframe(df)
    return df

# Preprocess the data (remove unnecessary columns, clean up, and convert ranks to numeric)
def preprocess_dataframe(df):
    df.dropna(axis=1, how='all', inplace=True)  # Drop columns with all NaNs
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
    
    # Convert Opening Rank and Closing Rank columns to numeric, forcing errors to NaN
    df['Opening Rank'] = pd.to_numeric(df['Opening Rank'], errors='coerce')
    df['Closing Rank'] = pd.to_numeric(df['Closing Rank'], errors='coerce')
    
    df.rename(columns={
        'Institute': 'College Name',
        'Academic Program Name': 'Course Name',
        'Quota': 'Quota',
        'Seat Type': 'Seat Type',
        'Gender': 'Gender',
        'Opening Rank': 'Opening Rank',
        'Closing Rank': 'Closing Rank'
    }, inplace=True)
    
    # Remove rows where Opening or Closing Rank is NaN (so no errors occur during comparison)
    df = df.dropna(subset=['Opening Rank', 'Closing Rank'])
    
    return df

# Function to calculate the chances of admission
def calculate_chances(user_rank, opening_rank, closing_rank):
    if user_rank <= opening_rank:
        return 100  # 100% chance if the rank is better than the opening rank
    elif user_rank > closing_rank:
        return 0  # 0% chance if the rank is worse than the closing rank
    else:
        # Calculate chance as a percentage between the opening and closing ranks
        return int(100 * (closing_rank - user_rank) / (closing_rank - opening_rank))

# Function to filter courses based on user selection
def filter_courses(df, course_type):
    if course_type == "B.Plan (Planning-related)":
        return df[df['Course Name'].str.contains('planning', case=False, na=False)]
    elif course_type == "B.Arch (Architecture-related)":
        return df[df['Course Name'].str.contains('architecture|design', case=False, na=False)]
    else:  # B.Tech for all other courses
        return df[~df['Course Name'].str.contains('planning|architecture|design', case=False, na=False)]

# Algorithm to classify colleges into 'Ambitious', 'Moderate', and 'Safe'
def classify_colleges(df, user_rank, quota, seat_type):
    # Ensure all columns are numeric for comparison
    df['Opening Rank'] = pd.to_numeric(df['Opening Rank'], errors='coerce')
    df['Closing Rank'] = pd.to_numeric(df['Closing Rank'], errors='coerce')
    
    # Create a copy of the DataFrame to add the "Chance" column
    df = df.copy()
    
    # Calculate chances only for valid numeric values
    df['Chance'] = df.apply(
        lambda row: calculate_chances(user_rank, row['Opening Rank'], row['Closing Rank']) 
        if pd.notnull(row['Opening Rank']) and pd.notnull(row['Closing Rank']) 
        else 0, 
        axis=1
    )
    
    # Filter DataFrame according to user rank, quota, and seat type
    ambitious = df[(df['Closing Rank'] < user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    moderate = df[(df['Opening Rank'] <= user_rank) & (df['Closing Rank'] >= user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    safe = df[(df['Opening Rank'] > user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    
    return ambitious, moderate, safe

# Main Streamlit app
def main():
    st.title('College Predictor')

    # User inputs
    year = st.selectbox('Select Year:', [2023, 2024])
    user_rank = st.number_input('Enter your Rank:', min_value=0, step=1)

    # Load the correct data file based on the selected year
    if year == 2023:
        file_path = Path(__file__).parent / 'JOSSA 2023.xlsx'
    else:
        file_path = Path(__file__).parent / 'JosAA file final 2024.xlsx'

    df = load_data(file_path)

    # User inputs for quota, seat type, and course type
    quota = st.selectbox('Select your Quota:', df['Quota'].unique())
    seat_type = st.selectbox('Select your Seat Type:', df['Seat Type'].unique())
    course_type = st.selectbox('Select Course Type:', ['B.Plan (Planning-related)', 'B.Arch (Architecture-related)', 'B.Tech (Engineering-related)'])

    # Filter courses based on user selection
    df = filter_courses(df, course_type)

    # Predict button
    if st.button('Predict Colleges'):
        ambitious, moderate, safe = classify_colleges(df, user_rank, quota, seat_type)

        # Order by Opening Rank (lower cutoff is better)
        ambitious = ambitious.sort_values(by='Opening Rank')
        moderate = moderate.sort_values(by='Opening Rank')
        safe = safe.sort_values(by='Opening Rank')

        # Display results for Safe, Moderate, and Ambitious categories
        st.write("### Safe Colleges")
        if not safe.empty:
            safe['Chance (%)'] = safe['Chance']
            st.dataframe(safe[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank', 'Chance (%)']])
        else:
            st.write("No Safe Colleges found based on your rank.")

        st.write("### Moderate Colleges")
        if not moderate.empty:
            moderate['Chance (%)'] = moderate['Chance']
            st.dataframe(moderate[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank', 'Chance (%)']])
        else:
            st.write("No Moderate Colleges found based on your rank.")

        st.write("### Ambitious Colleges")
        if not ambitious.empty:
            ambitious['Chance (%)'] = ambitious['Chance']
            st.dataframe(ambitious[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank', 'Chance (%)']])
        else:
            st.write("No Ambitious Colleges found based on your rank.")

if __name__ == '__main__':
    main()
