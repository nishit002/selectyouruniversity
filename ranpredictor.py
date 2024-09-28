import streamlit as st
import pandas as pd
import pkg_resources

# Function to load and process the Excel data from the repository
@st.cache
def load_data(file_path):
    # Use pkg_resources to load the file from the package
    stream = pkg_resources.resource_stream(__name__, file_path)
    df = pd.read_excel(stream)
    df = preprocess_dataframe(df)
    return df

# Preprocess the data (remove unnecessary columns, clean up)
def preprocess_dataframe(df):
    df.dropna(axis=1, how='all', inplace=True)  # Drop columns with all NaNs
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
    df.rename(columns={
        'Institute': 'College Name',
        'Academic Program Name': 'Course Name',
        'Quota': 'Quota',
        'Seat Type': 'Seat Type',
        'Gender': 'Gender',
        'Opening Rank': 'Opening Rank',
        'Closing Rank': 'Closing Rank'
    }, inplace=True)
    return df

# Algorithm to classify colleges into 'Ambitious', 'Moderate', and 'Safe'
def classify_colleges(df, user_rank, quota, seat_type):
    ambitious = df[(df['Closing Rank'] < user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    moderate = df[(df['Opening Rank'] <= user_rank) & (df['Closing Rank'] >= user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    safe = df[(df['Opening Rank'] > user_rank) & (df['Quota'] == quota) & (df['Seat Type'] == seat_type)]
    return ambitious, moderate, safe

# Main Streamlit app
def main():
    st.title('College Predictor')

    # Load data from the repository using pkg_resources
    file_2023 = 'selectyouruniversity/JOSSA 2023.xlsx'  # Path to the 2023 file
    file_2024 = 'selectyouruniversity/JosAA file final 2024.xlsx'  # Path to the 2024 file

    # Select the file based on user preference
    file_path = st.selectbox('Select the data file to use:', ['JOSSA 2023', 'JosAA file final 2024'])

    if file_path == 'JOSSA 2023':
        df = load_data(file_2023)
    else:
        df = load_data(file_2024)

    # User inputs
    user_rank = st.number_input('Enter your Rank:', min_value=0, step=1)
    quota = st.selectbox('Select your Quota:', df['Quota'].unique())
    seat_type = st.selectbox('Select your Seat Type:', df['Seat Type'].unique())

    # Predict button
    if st.button('Predict Colleges'):
        ambitious, moderate, safe = classify_colleges(df, user_rank, quota, seat_type)

        # Display results
        st.write("### Ambitious Colleges")
        st.dataframe(ambitious[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank']])

        st.write("### Moderate Colleges")
        st.dataframe(moderate[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank']])

        st.write("### Safe Colleges")
        st.dataframe(safe[['College Name', 'Course Name', 'Opening Rank', 'Closing Rank']])

if __name__ == '__main__':
    main()
