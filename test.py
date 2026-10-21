import streamlit as st
import pandas as pd
import time 
from datetime import date

st.sidebar.title("Battery Management System")
select_id = st.sidebar.selectbox("ID Type", ["Battery Pack Dummy ID", "Battery Pack ID", "BMS ID"])
if select_id=="Battery Pack Dummy ID":
    if st.button("Refresh"):
            st.rerun()
    st.title("HV Label Printing")
    st.header("Battery Pack Dummy ID")
    st.subheader("Serial Number")

    combo1 = st.selectbox("Combo", ["Value1", "Value 2", "value3"])
    st.text(f"you selected {combo1}")
    st.button("button1")
    st.write("Generate Labels") # similar to text
    st.write({"name": "Radar"})
    st.text("Sample Text")
    st.success("Labels Generated Successfully (Success)")
    st.error("Label Generation Failed (error) ")
    st.warning("Serial Number is Not Correct (Warning)")

    st.info("Waiting for Module Integration (Info)")

    if st.button("button2"):
        st.write("Button2 Response")
    
    text1 = st.text_input("Write Something (text_input)")
    st.write (text1)

    num_quantity = st.number_input("Quantity", min_value=1, max_value=100)
    st.write(num_quantity)

    text2 = st.text_area("Text2 (text_area)")
    st.write(text2)

    st.multiselect("multiselect", ["Select1", "Select2", "Select3"])

    check1 = st.checkbox('Integration Ok (checkbox)')
    st.text(f"status {check1}")

    radio1 = st.radio("rad1", ["R1", "R2", "R3"])
    st.write(f"you selected {radio1}")

    date1 = st.date_input("MFG Date (date_input)")

    datetime1 =st.datetime_input("MFG Datetime (datetime_input)")

    file_upload1 = st.file_uploader("Upload File1", type=["xlsx"])
    if file_upload1:
        st.write(f"{file_upload1.name} is uploaded successfully")
    if not file_upload1:
        st.write("Upload file above")
    
    image1 = st.image("C:/Users/RadarCalibration/Desktop/LABEL_PRINT/HV_LABEL_PRINT/HV_SC_NEW/models/hv/assets/logo.png")

    df = pd.DataFrame({ 
                       "Name": ["User1", "user2"],
                       "Age": ["20", "24"],
                       "Dept": ["ECE", "CSE"],
                       })
    st.dataframe(df)
    st.write(f"above is Pandas DataFrame")
    st.table(df)

    col1, col2 = st.columns(2)
    with col1:
        st.button("Print")
    
    with col2:
        st.button("Clear")
    if "serial_count" not in st.session_state:
        st.session_state.serial_count=0
    if st.button("Increment"):
        st.session_state.serial_count+=1
    if st.button("Decrement"):
        st.session_state.serial_count-=1
    st.write(st.session_state.serial_count)
    
    # with st.spinner("Waiting.."):
    #     time.sleep(5)
    # st.success("Done")
    
    # bar = st.progress(0)
    # for i in range(100):
    #     bar.progress(i+1)
    #     time.sleep(0.05)
    #     if i==100:
    #         st.write("Successfully Uploaded")
            
    with st.form("form1"):
        serial_number = st.text_input("Serial Number")
        submit_serial = st.form_submit_button("Submit")
        
        if submit_serial:
            st.write(f"Serial Number {serial_number} Submitted Successfully")
            
    scan = st.text_input("Scan barcode here", key="barcode")
    if scan:
        st.success(f"Scanned {scan}")
        

    # from common.nomenclature.serial_number import (
    #     build_serial_number,
    #     parse_serial_number,
    # )

    # st.set_page_config(
    #     page_title="HV Serial Number Manager",
    #     layout="wide"
    # )

    # st.title("HV Serial Number Manager")

    # tab1, tab2 = st.tabs(
    #     ["Generate Serial Number", "Parse Serial Number"]
    # )

    # with tab1:

    #     st.subheader("Generate Serial Number")

    #     col1, col2 = st.columns(2)

    #     with col1:

    #         plant = st.selectbox(
    #             "Plant",
    #             ["jigani", "domlur", "plant_c"]
    #         )

    #         model = st.selectbox(
    #             "Model",
    #             [
    #                 "low voltage",
    #                 "high voltage",
    #                 "shockwave",
    #                 "tesseract"
    #             ]
    #         )

    #         variant = st.selectbox(
    #             "Variant",
    #             [
    #                 "12P",
    #                 "16P",
    #                 "24P",
    #                 "27P"
    #             ]
    #         )

    #         line = st.selectbox(
    #             "Line",
    #             [
    #                 "1",
    #                 "2",
    #                 "3"
    #             ]
    #         )

    #     with col2:

    #         category = st.selectbox(
    #             "Category",
    #             [
    #                 "domestic",
    #                 "export"
    #             ]
    #         )

    #         cell_mfr = st.selectbox(
    #             "Cell Manufacturer",
    #             [
    #                 "molical",
    #                 "samsung",
    #                 "bak",
    #                 "eve",
    #                 "lg",
    #                 "ten power"
    #             ]
    #         )

    #         mfg_date = st.date_input(
    #             "Manufacturing Date",
    #             value=date.today()
    #         )

    #         serial_count = st.text_input(
    #             "Serial Count",
    #             value="00001"
    #         )

    #     if st.button("Generate Serial Number"):

    #         try:

    #             serial_no = build_serial_number(
    #                 plant=plant,
    #                 line=line,
    #                 when=mfg_date,
    #                 serial_count=serial_count,
    #                 model=model,
    #                 variant=variant,
    #                 cell_mfr=cell_mfr,
    #                 category=category,
    #             )

    #             st.success("Serial Number Generated")

    #             st.code(
    #                 serial_no,
    #                 language="text"
    #             )

    #         except Exception as e:

    #             st.error(str(e))

    # # -----------------------------
    # # PARSE SERIAL NUMBER
    # # -----------------------------
    # with tab2:

    #     st.subheader("Parse Serial Number")

    #     scanned_serial = st.text_input(
    #         "Scan / Enter Serial Number",
    #         placeholder="ABA31202510171P00001"
    #     )

    #     if st.button("Parse"):

    #         result = parse_serial_number(
    #             scanned_serial
    #         )

    #         if result is None:

    #             st.error(
    #                 "Invalid Serial Number"
    #             )

    #         else:

    #             st.success(
    #                 "Serial Number Parsed Successfully"
    #             )

    #             col1, col2 = st.columns(2)

    #             with col1:

    #                 st.text_input(
    #                     "Plant",
    #                     value=result.plant,
    #                     disabled=True
    #                 )

    #                 st.text_input(
    #                     "Model",
    #                     value=result.model,
    #                     disabled=True
    #                 )

    #                 st.text_input(
    #                     "Variant",
    #                     value=result.variant,
    #                     disabled=True
    #                 )

    #                 st.text_input(
    #                     "Line",
    #                     value=result.line,
    #                     disabled=True
    #                 )

    #             with col2:

    #                 st.text_input(
    #                     "Category",
    #                     value=result.category,
    #                     disabled=True
    #                 )

    #                 st.text_input(
    #                     "Cell Manufacturer",
    #                     value=result.cell_mfr,
    #                     disabled=True
    #                 )

    #                 st.text_input(
    #                     "Serial Count",
    #                     value=result.serial_count,
    #                     disabled=True
    #                 )

    #                 st.text_input(
    #                     "Manufacturing Date",
    #                     value=result.format_date(),
    #                     disabled=True
    #                 )

    # # -----------------------------
    # # LIVE SCANNER SECTION
    # # -----------------------------
    # st.divider()

    # st.subheader("Live Scanner")

    # scanner_value = st.text_input(
    #     "Scan Barcode Here",
    #     key="scanner_box"
    # )

    # if scanner_value:

    #     parsed = parse_serial_number(
    #         scanner_value
    #     )

    #     if parsed:

    #         st.success("Valid Serial Number")

    #         st.write(
    #             {
    #                 "Plant": parsed.plant,
    #                 "Model": parsed.model,
    #                 "Variant": parsed.variant,
    #                 "Category": parsed.category,
    #                 "Cell Manufacturer": parsed.cell_mfr,
    #                 "Manufacturing Date": parsed.format_date(),
    #                 "Serial Count": parsed.serial_count,
    #             }
    #         )

    #     else:

    #         st.error(
    #             "Invalid Serial Number"
    #         )