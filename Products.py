import streamlit as st
import pandas as pd
import os.path

#uploader to input new database from shopify
input_cvs = st.file_uploader(label = "Upload Shopify database here", type = 'csv')

#read previous dataframe for comparison
previous_df = pd.read_csv('prev_checked.csv', index_col=0)


def dataframe_without_selections(df):
    df_without_selections = df.copy()
    if "Status" in df:
        df_without_selections = df_without_selections.drop(columns=['Status'])
    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_without_selections,
        hide_index=True,
        disabled=df.columns,
    )

if input_cvs is None:
    st.write("No file uploaded")

else:
    #filter shopify database
    df = pd.read_csv(input_cvs)
    df = df[df["Variant Inventory Qty"].notna()]
    df = df.astype({'Variant Inventory Qty':'int'})
    df = df[df["Status"] == "active"]
    df = df[(df["Variant Inventory Qty"] < 3 )]
    df = df[(df["Variant Inventory Qty"] >= 0 )]
    df = df[["Variant SKU", "Title", "Variant Inventory Qty", "Status"]]

    #create two columns
    data_container = st.container()
    with data_container:
        show_df, older_df = st.columns(2)
    with show_df:
        st.subheader("Shopify database:")
        show_df = dataframe_without_selections(df)
        st.write(len(df.index))
    with older_df:
        if previous_df.empty:
            st.subheader("Previously checked:")
            st.write("you didn't check anything yet!")
        else:
            st.subheader("Previously checked:")
            older_df = dataframe_without_selections(previous_df)
            st.write(len(previous_df.index))


    if previous_df.empty:
        result = df
        result["Previous_Qty"] = ""

    else:
        merge = df.merge(previous_df, on=['Variant SKU', 'Title'], how='left', indicator='Exists')
        merge = merge.drop(columns=['Exists'])
        result = merge
    result = result.drop(columns=['Status'])
    result = result.rename(columns={"Variant Inventory Qty_x": "Variant Inventory Qty", "Variant Inventory Qty_y": "Previous_Qty"})
    result = result[result['Variant Inventory Qty'] != result['Previous_Qty']]

    def dataframe_with_selections(df):
        df_with_selections = df.copy()
        df_with_selections.insert(0, "Select", False)

        # Get dataframe row-selections from user with st.data_editor
        edited_df = st.data_editor(
            df_with_selections,
            hide_index=True,
            column_config={"Select": st.column_config.CheckboxColumn(required=True)},
            disabled=df.columns,
        )

        # Filter the dataframe using the temporary column, then drop the column
        selected_rows = edited_df[edited_df.Select]
        selected_rows = selected_rows.drop(columns=['Previous_Qty'])
        return selected_rows.drop('Select', axis=1)

    st.subheader('Needs Checking:')
    selection = dataframe_with_selections(result)
    st.write(len(result.index))
    st.subheader("Checked:")
    st.write(selection)

    prev_checked = pd.DataFrame(selection)

    def update_df():
        previous_df = pd.read_csv('prev_checked.csv', index_col=0)
        merge2 = previous_df.merge(prev_checked, on=['Variant SKU', 'Title', 'Variant Inventory Qty'], how='left')
        merge2. reset_index(drop=True)
        merge2 = merge2[["Variant SKU", "Title", "Variant Inventory Qty"]]
        merge2 = pd.concat([prev_checked, previous_df])
        merge2.drop_duplicates(subset=['Variant SKU', 'Title'], keep="first", inplace=True)
        merge2.to_csv(os.path.join('/Users/ymoh/Desktop/Voltaat_product_replicas/','prev_checked.csv'))

    if st.button('Save', on_click=update_df):
        st.write('Saved!')
