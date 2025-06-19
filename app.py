import streamlit as st
import pandas as pd
import os

# Load master data and response history
@st.cache_data
def load_master():
    return pd.read_csv("master_space_data.csv")

@st.cache_data
def load_options():
    df = pd.read_csv("options.csv")
    df.columns = df.columns.str.strip()
    df = df.dropna()
    df["SPACE CATEGORY"] = df["SPACE CATEGORY"].str.strip()
    df["SPACE TYPE"] = df["SPACE TYPE"].str.strip()
    df["SPACE NAME"] = df["SPACE NAME"].str.strip()
    return df

def load_responses():
    if os.path.exists("responses.csv"):
        df = pd.read_csv("responses.csv")
        if "ID" not in df.columns:
            df["ID"] = None  # ensure fallback column exists
        return df
    else:
        #return pd.DataFrame(columns=["ID", "New Category", "New Type", "New Name"])
        return pd.DataFrame(columns=["ID", "Old Space Name", "Old Type", "Old Category", "Department","New Space Name", "New Type", "New Category", "New Space Alias Name"])
# Load data
master_df = load_master()
options_df = load_options()
responses_df = load_responses()

# Compute progress
total_records = len(master_df)
completed_records = len(responses_df["ID"].unique())
skipped_records = len(st.session_state.skipped_ids) if "skipped_ids" in st.session_state else 0
progress_pct = completed_records / total_records if total_records else 0

# Display progress
st.markdown(f"### 📊 Progress Overview")
st.markdown(f"""
- ✅ **Completed:** {completed_records}  
- ⏭️ **Skipped (this session):** {skipped_records}  
- 📦 **Total Records:** {total_records}
""")
st.progress(progress_pct)


# Track skipped IDs in session
if "skipped_ids" not in st.session_state:
    st.session_state.skipped_ids = set()

if "alias_name" not in st.session_state:
    st.session_state.alias_name = ""

# Find the next unfilled record
filled_ids = set(responses_df["ID"].unique())
unfilled_df = master_df[
    ~master_df["ID"].isin(filled_ids.union(st.session_state.skipped_ids))
]


if unfilled_df.empty:
    st.success("🎉 All records have been completed!")
    st.stop()

# Display first unfilled record
record = unfilled_df.iloc[0]
st.markdown("### 🧾 Review Record")
st.write(f"**Old Space Name:** {record['space_alias_name']}")
st.write(f"**Old Category:** {record['space_category']}")
st.write(f"**Old Type:** {record['space_type']}")
st.write(f"**Department:** {record['department_occupied']}")
# Optional alias input
st.markdown("### 🏷️ Optional Alias")

# Reset alias if the record has changed
if st.session_state.get("current_id") != record["ID"]:
    st.session_state.alias_name = ""
    st.session_state.current_id = record["ID"]

alias_name = st.text_input("New Space Alias Name (Optional)", value=st.session_state.alias_name)


# category_options = sorted(options_df["SPACE CATEGORY"].unique())
# selected_cat = st.selectbox("New Category", category_options)

# type_options = sorted(options_df[options_df["SPACE CATEGORY"] == selected_cat]["SPACE TYPE"].unique())
# selected_type = st.selectbox("New Type", type_options)

# name_options = sorted(options_df[(options_df["SPACE CATEGORY"] == selected_cat) & (options_df["SPACE TYPE"] == selected_type)]["SPACE NAME"].unique())
# selected_name = st.selectbox("New Name", name_options)


# Cascading dropdowns
st.markdown("### ✏️ Reclassification Input")

# Get all categories for filtering
category_options = sorted(options_df["SPACE CATEGORY"].unique())

# Determine all possible name options first
name_options = sorted(options_df["SPACE NAME"].unique())
selected_name = st.selectbox("New Name", name_options)

# Now filter type/category based on selected name
filtered_by_name = options_df[options_df["SPACE NAME"] == selected_name]

type_options = sorted(filtered_by_name["SPACE TYPE"].unique())
selected_type = st.selectbox("New Type", type_options)

category_options_filtered = sorted(filtered_by_name["SPACE CATEGORY"].unique())
selected_cat = st.selectbox("New Category", category_options_filtered)


# ─────────────────────────────────────────────
# 🔘 Submit & Skip Buttons
# ─────────────────────────────────────────────

st.markdown("### ✅ Actions")

col1, col2 = st.columns([1, 1])

# ✅ SUBMIT BUTTON
with col1:
    if st.button("✅ Submit"):
        result = {
            "ID": record["ID"],
            "Old Space Name": record["space_alias_name"],
            "Old Type": record["space_type"],
            "Old Category": record["space_category"],
            "Department": record["department_occupied"],
            "New Space Name": selected_name,
            "New Type": selected_type,
            "New Category": selected_cat,
            "New Space Alias Name": alias_name.strip()
        }

        new_row = pd.DataFrame([result])

        # Save it
        if os.path.exists("responses.csv"):
            write_header = os.stat("responses.csv").st_size == 0
            new_row.to_csv("responses.csv", mode='a', header=write_header, index=False)
        else:
            new_row.to_csv("responses.csv", mode='w', header=True, index=False)

        
        st.success("✅ Response recorded. Loading next record...")
        st.session_state.alias_name = ""
        st.rerun()

# ⏭️ SKIP BUTTON
with col2:
    if st.button("⏭️ Skip"):
        st.session_state.skipped_ids.add(record["ID"])
        st.rerun()




st.markdown("---")
st.markdown("### 🧱 Add New Hierarchy Entry (Optional)")

with st.expander("➕ Add Hierarchy"):
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        new_space_name = st.text_input("New Space Name")
    with col_b:
        new_space_type = st.text_input("New Space Type")
    with col_c:
        new_space_category = st.text_input("New Space Category")

    if st.button("💾 Submit New Hierarchy Entry"):
        if all([new_space_name.strip(), new_space_type.strip(), new_space_category.strip()]):
            new_entry = pd.DataFrame([{
                "SPACE NAME": new_space_name.strip(),
                "SPACE TYPE": new_space_type.strip(),
                "SPACE CATEGORY": new_space_category.strip()
            }])
            if os.path.exists("options.csv"):
                new_entry.to_csv("options.csv", mode='a', header=False, index=False)
            else:
                new_entry.to_csv("options.csv", mode='w', header=True, index=False)

            # Invalidate cache to load updated options.csv
            load_options.clear()
            st.success("✅ New hierarchy entry added successfully!")
            st.rerun()
        else:
            st.warning("⚠️ Please fill in all three fields before submitting.")

if os.path.exists("responses.csv"):
    with open("responses.csv", "rb") as f:
        st.download_button("⬇️ Download responses.csv", f, file_name="responses.csv")

st.markdown("---")
if st.button("❌ Kill App / End Session"):
    st.session_state.clear()  # optional: reset memory
    st.warning("🚫 The session has been terminated. You can now close the browser tab.")
    st.stop()
