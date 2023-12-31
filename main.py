import streamlit as st
from Sondir import Robertson1990
import pandas as pd
from PIL import Image
img_robertson = Image.open('grafik_robertson.png')
img_contoh = Image.open('contoh_data.png')

table_lunne = {
    "Zona": [1,2,3,4,5,6,7,8,9],
    "Jenis tanah": ["Butiran halus, sensitive", "Lempung - Tanah organik","Lempung: lempung - lempung berlanau","Lanau mix: lanau berlempung - lempung berlanau","Pasir mix: pasir berlanau - lanau berpasir","Pasir: Pasir - Pasir berlanau","Pasir padat - Pasir berkerikil", "Pasir kaku - pasir berlempung (overconsolidate)","Sangat kaku, berbutir halus"],
    "Berat isi [kN/m3]": [17.5,12.5,17.5,18,18.5,19.0,20.0,20.5,19.0]
}

df_lunne = pd.DataFrame(table_lunne)

st.set_page_config(layout="wide")
st.header("Sondir v.01")

st.write("*Sondir Mekanikal - Bikonus*")

with st.sidebar:
    st.subheader("Import Data Sondir:")
    uploaded_file = st.file_uploader("File excel .xlsx",type="xlsx")
    input_mat = st.number_input("Kedalaman muka air tanah (MAT)", value=999.0, min_value=0.0)

tab1, tab2, tab3 = st.tabs(["Profil Tanah", "Kapasitas Dukung", "Teori"])

if uploaded_file is None:
    with tab1:
        st.write("Klik **[Browse files]** untuk memasukkan data sondir dalam format excel.")
        st.markdown("""
                Dalam file excel tersebut harus memiliki tiga (3) parameter yaitu:
                 
                - kedalaman, z [m]
    
                - tahanan konus, qc [Kg/cm2]
    
                - tahanan selimut, fs [Kg/cm2]
    
                """)
        st.write("**Berikut contoh isi file excel untuk input data:**")
        st.image(img_contoh,width=300)
        st.write("Download contoh file data sondir [Download](https://www.dropbox.com/scl/fi/r3wf0ejkkxb6hfibcqwzn/data_sondir.xlsx?rlkey=fs3ufz1isrn0dj7g2j0zk55ke&dl=0) atau [Download](https://docs.google.com/spreadsheets/d/1RA-K24C7r_1fTgX65MGyJ8XyTbyZxbhu/edit?usp=sharing&ouid=101300635660345969319&rtpof=true&sd=true)")
else:
    if input_mat == 999:
        mat = None
    else:
        mat = input_mat
    cpt = Robertson1990(file_path = uploaded_file, mat=mat)
    cpt.solve()
    cpt.soil_profil()
    fig_qc = cpt.plot(idx=0,color="red") # qc
    fig_fs = cpt.plot(idx=1,color="blue") # fs
    fig_Rf = cpt.plot(idx=2,color="green") # Rf
    fig_profil = cpt.soil_profil()
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.plotly_chart(fig_qc,use_container_width=True)
        with col2:
            st.plotly_chart(fig_fs,use_container_width=True)
        with col3:
            st.plotly_chart(fig_Rf,use_container_width=True)
        with col4:
            st.plotly_chart(fig_profil,use_container_width=True)

        st.divider()
        st.subheader("Tabel:")
        st.dataframe(cpt.df,hide_index=True)

        csv1 = cpt.df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Tabel Profil Tanah",
            csv1,
            "profil_tanah.csv",
            "csv"
            )
        
    with tab2:
        st.write("**[Hanya berlaku untuk pondasi telapak pada tanah pasir]**")
        col3, col4, col5 = st.columns(3)
        with col3:
            Bmin = st.number_input("Lebar minimum, $B_{min}$ [m]", value=0.8)
        with col4:
            Bmax = st.number_input("Lebar maksimum, $B_{max}$ [m]", value=2)

        cpt.solve_qa(Bmin=Bmin,Bmax=Bmax)
        with col5:
            list_lebar = list(cpt.df_qa.columns)[1:]
            lebar = st.selectbox(
                "Pilih lebar pondasi",
                list_lebar,
                index=0,
            )
        with col3:
            fig = cpt.plot_all_qa()
            st.plotly_chart(fig,use_container_width=True)
        with col5:
            fig = cpt.plot_qa(param=lebar)
            st.plotly_chart(fig,use_container_width=True)
        with col4:
            st.plotly_chart(fig_profil,use_container_width=True)
        
        st.divider()
        st.subheader("Tabel Kapasitas Dukung:")
        st.dataframe(cpt.df_qa,hide_index=True)

        csv2 = cpt.df_qa.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Tabel Kapasitas Dukung",
            csv2,
            "kapasitas_dukung.csv",
            "csv"
            )
    
with tab3:
    col6, col7 = st.columns([0.6, 0.4])

    with col6:
        st.subheader("Profil Lapisan Tanah")
        st.markdown("""
                    Profil lapisan tanah diperoleh dengan cara plot paramater $q_c / p_a$ dan $R_f$ pada grafik Robertson 1990.
                    
                    Dimana:

                    - $q_c$ = tahanan konus [kPa]

                    - $p_a$ = tekanan atmosfir = 100 [kPa]

                    - $R_f$ = rasio friksi = $f_s / q_c$ [%]
                    
        """)

        st.subheader("Kapasitas dukung Pondasi Telapak")
        st.markdown("""
                    Kapasitas dukung ijin [$q_a$], dihitung berdasarkan rumus Meyerhof (1956). Kapasitas dukung ijin ini didasarkan pada penurunan pondasi sebesar 1 inch [2.54 cm].

                    **Kapasitas dukung ini hanya berlaku untuk fondasi dangkal pada tanah pasir**.
                    """
                    )
        r"""$q_a = \frac{q_c}{30}$ untuk $B \leq 1.2 m$"""
        
        r"""$q_a = \frac{q_c}{30} \left( \frac{B+0.3}{B} \right)^2$ untuk $B \ge 1.2 m$"""         

        st.markdown("""
            
                    Dimana:

                    - $q_a$ = kapasitas dukung ijin pondasi telapak [kPa]

                    - $B$ = lebar pondasi [m]
                    
        """)
    with col7:
        st.subheader("SBTn zone Robertson (1990)")
        st.image(img_robertson,width=360)
        
        st.subheader("Berat isi tanah (Lunne et al., 1997)")
        st.dataframe(df_lunne,hide_index=True)
