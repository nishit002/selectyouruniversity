import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path

# Set page config for title and logo
st.set_page_config(page_title="JEE Main College Predictor 2024", page_icon="https://i.imgur.com/pctn0tc.png")

# Function to load and process the Excel data
@st.cache
def load_data():
    # Load data from both years
    df_2023 = pd.read_excel(Path(__file__).parent / 'JOSSA 2023.xlsx')
    df_2024 = pd.read_excel(Path(__file__).parent / 'JosAA file final 2024.xlsx')
    
    # Combine both years' data
    df = pd.concat([df_2023, df_2024], ignore_index=True)
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

# Function to calculate the chances of admission (with more realistic values)
def calculate_chances(user_rank, opening_rank, closing_rank):
    if user_rank <= opening_rank:
        return 90  # Cap the maximum chance at 90%
    elif user_rank > closing_rank:
        return 10  # Set a minimum realistic chance at 10%
    else:
        # Calculate chance as a percentage between the opening and closing ranks
        return int(10 + 80 * (closing_rank - user_rank) / (closing_rank - opening_rank))

# Function to calculate deviation from last year's cutoff
def calculate_deviation(user_rank, closing_rank):
    return user_rank - closing_rank  # Positive value means the user is above last year's cutoff

# Function to filter courses based on user selection
def filter_courses(df, course_type):
    if course_type == "B.Plan / B.Arch":
        return df[df['Course Name'].str.contains('planning|architecture|design', case=False, na=False)]
    else:  # B.Tech for all other courses
        return df[~df['Course Name'].str.contains('planning|architecture|design', case=False, na=False)]

# Algorithm to classify colleges into 'Ambitious', 'Moderate', and 'Safe'
def classify_colleges(df, user_rank, quota, seat_type):
    # Ensure all columns are numeric for comparison
    df['Opening Rank'] = pd.to_numeric(df['Opening Rank'], errors='coerce')
    df['Closing Rank'] = pd.to_numeric(df['Closing Rank'], errors='coerce')
    
    # Create a copy of the DataFrame to add the "Chance" and "Deviation" columns
    df = df.copy()
    
    # Calculate chances and deviation from last year's cutoff
    df['Chance'] = df.apply(
        lambda row: calculate_chances(user_rank, row['Opening Rank'], row['Closing Rank']) 
        if pd.notnull(row['Opening Rank']) and pd.notnull(row['Closing Rank']) 
        else 0, 
        axis=1
    )
    
    df['Deviation'] = df.apply(
        lambda row: calculate_deviation(user_rank, row['Closing Rank'])
        if pd.notnull(row['Closing Rank'])
        else 0,
        axis=1
    )
    
    # Filter DataFrame according to user rank, quota, and seat type
    ambitious = df[(df['Closing Rank'] < user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    moderate = df[(df['Opening Rank'] <= user_rank) & (df['Closing Rank'] >= user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    safe = df[(df['Opening Rank'] > user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    
    return ambitious, moderate, safe

# Function to download result in Excel
def create_download_link(df, filename="prediction_results.xlsx"):
    output = BytesIO()
    
    # Use ExcelWriter to write the DataFrame to an Excel file in memory
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
        writer.close()  # Correct way to close the writer in newer versions of pandas
    
    # Move the pointer to the beginning of the stream
    output.seek(0)
    
    # Create the download button
    st.download_button(
        label="Download Results as Excel",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Main Streamlit app
def main():
    st.image("https://i.imgur.com/pctn0tc.png", width=200)  # Correct Imgur URL for the logo
    st.title('JEE Main College Predictor 2024')

    # Lead form to collect user data
    with st.form("lead_form"):
        st.write("### Please fill out your information:")
        name = st.text_input("Name", value="")
        email = st.text_input("Email", value="")
        phone = st.text_input("Phone Number", value="")
        city = st.text_input("City", value="")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if not name or not email or not phone or not city:
                st.warning("Please fill out all fields.")
            else:
                st.success(f"Thanks {name}, your details have been submitted!")
    
    # User inputs for the prediction (rank field empty initially)
    user_rank = st.number_input('Enter your Rank (required):', min_value=1, step=1, format="%d", key="rank", value=None)

    # Load the data from both years
    df = load_data()

    # Radio button for course type selection with B.Tech as the default
    course_type = st.radio('Select Course Type:', ['B.Tech', 'B.Plan / B.Arch'], index=0)

    # User inputs for quota and seat type
    quota = st.selectbox('Select your Quota:', df['Quota'].unique())
    seat_type = st.selectbox('Select your Seat Type:', df['Seat Type'].unique())

    # Filter courses based on user selection
    df = filter_courses(df, course_type)

    # Predict button
    if st.button('Predict Colleges'):
        st.write("### Prediction Results:")

        # Classify colleges based on user inputs
        ambitious, moderate, safe = classify_colleges(df, user_rank, quota, seat_type)

        # Display results for Safe, Moderate, and Ambitious categories
        st.write("### Safe Colleges")
        if not safe.empty:
            safe['Chance (%)'] = safe['Chance']
            safe['Deviation from Last Year Cutoff'] = safe['Deviation']
            st.dataframe(safe[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank', 'Chance (%)', 'Deviation from Last Year Cutoff']])
        else:
            st.write("No Safe Colleges found based on your rank.")

        st.write("### Moderate Colleges")
        if not moderate.empty:
            moderate['Chance (%)'] = moderate['Chance']
            moderate['Deviation from Last Year Cutoff'] = moderate['Deviation']
            st.dataframe(moderate[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank', 'Chance (%)', 'Deviation from Last Year Cutoff']])
        else:
            st.write("No Moderate Colleges found based on your rank.")

        st.write("### Ambitious Colleges")
        if not ambitious.empty:
            ambitious['Chance (%)'] = ambitious['Chance']
            ambitious['Deviation from Last Year Cutoff'] = ambitious['Deviation']
            st.dataframe(ambitious[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank', 'Chance (%)', 'Deviation from Last Year Cutoff']])
        else:
            st.write("No Ambitious Collegesfound based on your rank.")

        # Combine results into a DataFrame for downloading
        result_df = pd.concat([
            safe.assign(Category='Safe'),
            moderate.assign(Category='Moderate'),
            ambitious.assign(Category='Ambitious')
        ])

        # Provide download button for the Excel file
        create_download_link(result_df)

if __name__ == '__main__':
    main()
