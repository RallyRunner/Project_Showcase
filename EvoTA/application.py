import streamlit as st
import pandas as pd
import assignments_upload
from pathlib import Path

#read necessary files
path = Path(__file__).parent

with open(path / "instructions/instructions.txt", mode ="r") as file:
    txt_instructions = file.read()

sections_example = pd.read_csv(path / "instructions/sections.csv")
tas_example = pd.read_csv(path / "instructions/tas.csv")

#necessary functions
def view_result():
    results_df = pd.read_csv(path / "results/summary.csv")
    results_df = results_df[(results_df.conflicts == 0) & (results_df.unwilling == 0)]
    if f"solution{solution_value}" in results_df['solutions'].values:
        best_solution_df = pd.read_csv(path / f"results/best_solutions{solution_value}.csv", header=None)
        return best_solution_df
    else:
        st.write("Please enter a valid number following one of the solutions listed above.")

def solve(section_data, ta_data):
    assignments_upload.main(section_data, ta_data)
    try:
        solving_status = st.write("Solving. Please wait < 1 minute.")
        assignments_upload.main(section_data, ta_data)
    except:
        st.write("Error with inputted data. Please check for missing values.")

    # show on app
    results_df = pd.read_csv(path / "results/summary.csv")
    results_df = results_df[(results_df.conflicts == 0) & (results_df.unwilling == 0)]
    return results_df

#app building

#Title
st.title("TA Assigner App")

#Instructions
st.subheader("Instructions")
st.write(txt_instructions)
st.subheader("section.csv Example")
st.dataframe(sections_example.head())
st.subheader("tas.csv Example")
st.dataframe(tas_example.head())

#Section Data
#Need to include adjustable number of sections & save button
st.header('Section Data')
section_df = pd.DataFrame(columns = ["section","instructor","daytime","location","students","topic","min_ta","max_ta"])
section_df_edited = st.data_editor(section_df, hide_index=True, num_rows = "dynamic", use_container_width = True, key="section")
num_rows = len(section_df_edited.index)
#section_df_cols = section_df_edited.columns

#TA Data
st.header("TA Data")
"""Need to include adjustable number of TAs & auto adjust section to # of sections inputted"""
#create adjustable ta_cols
ta_cols = ["ta_id", "name", "max_assigned"]
for i in range(num_rows):
    ta_cols.append(str(i))

#create editable dataframe
ta_df = pd.DataFrame(columns= ta_cols)
ta_df_edited = st.data_editor(ta_df, hide_index=True, num_rows="dynamic", use_container_width=True, key = "ta")
#ta_df_cols = ta_df_edited.columns

#Upload Data
st.header("CSV Uploads")
section_df_upload = st.file_uploader("Input Section Data csv")
ta_df_upload = st.file_uploader("Input TA Schedule Data csv")

#Results
st.header("Results")
options = ["Inputted Tables", "Uploaded CSV"]
option = st.radio("Which method did you use?", options, key="radio_option")

if option == "Inputted Tables":
    # convert uploaded files into pd.dataframes
    section_data = pd.DataFrame(section_df_edited)
    # convert to proper data types
    section_data[["section","min_ta", "max_ta"]] = section_data[["section","min_ta", "max_ta"]].astype("int64")
    ta_data = pd.DataFrame(ta_df_edited)
    ta_data[["ta_id","max_assigned"]] = ta_data[["ta_id","max_assigned"]].astype("int64")

elif option == "Uploaded CSV":
    section_data = pd.read_csv(section_df_upload)
    ta_data = pd.read_csv(ta_df_upload)

solve_button = st.button("Solve", key = "solve")
if solve_button:
    results_df = solve(section_data, ta_data)
    st.session_state["summary"] = results_df

try:
    #st.dataframe(results_df)
    st.session_state["summary"]
except:
    st.write("Upload Files")

#view solution
with st.form(key="view_sol"):
    solution_value = st.number_input("Pick a solution to view", 0, 15)
    submit = st.form_submit_button('View Solution')
    if submit:
        best_sol = view_result()
        st.session_state["best_sol"] = best_sol

try:
    st.session_state["best_sol"]
except:
    st.write("Run Solver")


