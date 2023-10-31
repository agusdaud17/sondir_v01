"""
Package untuk mengolah data sondir berdasarkan Robertson 1990
"""

import pandas as pd
from scipy import signal, interpolate
from math import*
import numpy as np

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

# from scipy import interpolate
from PIL import Image

im = np.array(Image.open('SBTlow.jpg'))
x_logref = np.linspace(-1,1,1649)
x_grid = np.arange(0,1649,1)

Kg_cm = 0.0981 # MPa
to_kPa = 1000 # MPa

class Robertson1990:
    """docstring fo Sondir."""

    def __init__(self,id_="S-1", file_path=None, kPa=98.1, mat=None, gw=9.81):
        self.id_ = id_
        self.file_path = file_path
        self.df = pd.read_excel(self.file_path)
        self.kPa = kPa
        self.mat = mat
        self.gw = gw

    def zoneByColor(self,Rf,Qt):
        x_logref = np.linspace(-1,1,1649)
        x_grid = np.arange(0,1649,1)
        y_logref = np.linspace(0,3,1823)
        y_grid = np.arange(0,1823,1)

        if Qt > 1000:
            Qt = 999
        elif Qt <= 1:
            Qt = 1.1

        if Rf > 10:
            Rf = 9.9
        elif Rf <= 0.1:
            Rf = 0.105

        fx = interpolate.interp1d(x_logref, x_grid)
        fy = interpolate.interp1d(y_logref, y_grid)
        xg = int(fx(log10(Rf)))
        yg = int(fy(log10(Qt)))

        while True:
            color = im[-yg,xg]
            if color[1] == 222:
                zone = 1
                break
            elif color[1] == 105:
                zone = 2
                break
            elif color[1] == 123 or color[1] == 122:
                zone = 3
                break
            elif color[1] == 83:
                zone = 4
                break
            elif color[1] == 148:
                zone = 5
                break
            elif color[1] == 248 or color[1] == 247 or color[1] == 249:
                zone = 6
                break
            elif color[1] == 160:
                zone = 7
                break
            elif color[1] == 102:
                zone = 8
                break
            elif color[1] == 33:
                zone = 9
                break
            else:
                yg -= 1
        return zone

    def solve(self):
        self.df["Rf [%]"] = (self.df.iloc[:,2] / self.df.iloc[:,1]) * 100 # Rf = (qc/fs) * 100
        self.df["Rf [%]"][0] = 0
        self.df["qc_pa [-]"] = (self.df.iloc[:,1] * self.kPa) / 100 # qc/Pa
        self.df["Zona [-]"] = np.vectorize(self.zoneByColor)(self.df["Rf [%]"],self.df["qc_pa [-]"])
        self.df["Jenis Tanah [-]"] = np.vectorize(self.jenis_tanah)(self.df["Zona [-]"])

        self.df["qc [kPa]"] = round(self.df.iloc[:,1]*self.kPa, 2)
        self.df["Berat isi [kN/m3]"] = np.vectorize(self.berat_isi)(self.df["Zona [-]"])
        self.df["Zona [-]"][0] = None
        self.df["Jenis Tanah [-]"][0] = None
        self.solve_overburden()

        self.df["Su [kPa]"] = round((self.df["qc [kPa]"] - self.df["svo [kPa]"]) / 14, 2)
        self.solve_kepadatan()

    def solve_overburden(self):
        list_z = list(self.df.iloc[:,0])
        list_g = list(self.df["Berat isi [kN/m3]"])
        N_data = len(list_g)
        list_svo = [0]
        list_u = [0]
        list_svo_ef = [0]

        for i in range(1,N_data):
            g = list_g[i]
            z = list_z[i]
            dz = list_z[i] - list_z[i-1]

            u = 0
            if self.mat is not None and z > self.mat:
                u = (z-self.mat)*self.gw
            svo = list_svo[i-1] + (g*dz)
            svo_ef = svo - u

            list_svo.append(svo)
            list_u.append(u)
            list_svo_ef.append(svo_ef)

        self.df["svo [kPa]"] = list_svo
        self.df["u [kPa]"] = list_u
        self.df["svo_ef [kPa]"] = list_svo_ef

    def konsistensi(self,Su):
        if Su < 12:
            const = "Sangat lunak"
        elif Su < 25:
            const = "Lunak"
        elif Su < 50:
            const = "Agak kaku"
        elif Su < 100:
            const = "Kaku"
        elif Su < 200:
            const = "Sangat kaku"
        else:
            const = "Keras"
        return const

    def kepadatan_relatif(self,qc):
        qc = qc/1000
        if qc < 2:
            const = "Sangat lepas"
        elif qc < 4:
            const = "Lepas"
        elif qc < 12:
            const = "Padat sedang"
        elif qc < 20:
            const = "Padat"
        else:
            const = "Sangat padat"
        return const

    def solve_kepadatan(self):
        list_zona = list(self.df["Zona [-]"])
        list_qc = list(self.df["qc [kPa]"])
        list_su = list(self.df["svo [kPa]"])

        N_data = len(list_zona)

        zona_kohesif = [1,2,3,4,9]

        list_kepadatan = [None]

        for i in range(1,N_data):
            zona = list_zona[i]
            if zona in zona_kohesif:
                val = self.konsistensi(list_su[i])
            else:
                val = self.kepadatan_relatif(list_qc[i])
            list_kepadatan.append(val)

        self.df["Kepadatan/ konsistensi"] = list_kepadatan

    def solve_overburden(self):
        list_z = list(self.df.iloc[:,0])
        list_g = list(self.df["Berat isi [kN/m3]"])
        N_data = len(list_g)
        list_svo = [0]
        list_u = [0]
        list_svo_ef = [0]

        for i in range(1,N_data):
            g = list_g[i]
            z = list_z[i]
            dz = list_z[i] - list_z[i-1]

            u = 0
            if self.mat is not None and z > self.mat:
                u = (z-self.mat)*self.gw
            svo = list_svo[i-1] + (g*dz)
            svo_ef = svo - u

            list_svo.append(svo)
            list_u.append(u)
            list_svo_ef.append(svo_ef)

        self.df["svo [kPa]"] = list_svo

    def jenis_tanah(self,val):
        if val == 1:
            name = "Butiran halus, sensitive"
        elif val == 2:
            name = "Lempung - Tanah organik"
        elif val == 3:
            name = "Lempung: lempung - lempung berlanau"
        elif val == 4:
            name = "Lanau mix: lanau berlempung - lempung berlanau"
        elif val == 5:
            name = "Pasir mix: pasir berlanau - lanau berpasir"
        elif val == 6:
            name = "Pasir: Pasir - Pasir berlanau"
        elif val == 7:
            name = "Pasir padat - Pasir berkerikil"
        elif val == 8:
            name = "Pasir kaku - pasir berlempung (overconsolidate)"
        else:
            name = "Sangat kaku, berbutir halus"
        return name
        
    def berat_isi(self,val):
        if val == 1:
            g = 17.5
        elif val == 2:
            g = 12.5
        elif val == 3:
            g = 17.5
        elif val == 4:
            g = 18.0
        elif val == 5:
            g = 18.5
        elif val == 6:
            g = 19.0
        elif val == 7:
            g = 20.0
        elif val == 8:
            g = 20.05
        elif val == 9:
            g = 19.0
        else:
            g = 0
        return g
        
    def color_func(self,val):
        if val == 1:
            name = "Butiran halus, sensitive"
            color = 'rgb(255,0,0)'
        elif val == 2:
            name = "Lempung - Tanah organik"
            color = 'rgb(184,134,11)'
        elif val == 3:
            name = "Lempung: lempung - lempung berlanau"
            color = 'rgb(65,105,225)'
        elif val == 4:
            name = "Lanau mix: lanau berlempung - lempung berlanau"
            color = 'rgb(60,179,113)'
        elif val == 5:
            name = "Pasir mix: pasir berlanau - lanau berpasir"
            color = 'rgb(144,238,144)'
        elif val == 6:
            name = "Pasir: Pasir - Pasir berlanau"
            color = 'rgb(222,184,135)'
        elif val == 7:
            name = "Pasir padat - Pasir berkerikil"
            color = 'rgb(255,127,80)'
        elif val == 8:
            name = "Pasir kaku - pasir berlempung (overconsolidate)"
            color = 'rgb(128,128,128)'
        else:
            name = "Sangat kaku, berbutir halus"
            color = 'rgb(192,192,192)'
        return color, name

    def soil_profil(self,size=[800,350]):
        fig = go.Figure()

        for i in range(1,10):
            key = 'Zona [-]'
            df = self.df.loc[self.df[key] == i]
            if len(df[df.columns[0]]) > 0:
                color, name = self.color_func(i)
                fig.add_trace(go.Bar(x = df["Zona [-]"], y = df.iloc[:,0], name = name, width=0.25,orientation='h',marker_color=color,marker_line=dict(color=color)))

        fig.update_layout(title_text='Profil Lapisan Tanah')
        fig.update_layout(height=size[0], width=size[1], legend=dict(orientation="h"))
        fig.update_xaxes(side = "top", showgrid=False, showline=True, linewidth=2, linecolor='black')

        fig.update_yaxes(
            showgrid=True,
            title_text="Kedalaman Tanah (m)",
            ticks="outside",
            minor=dict(ticklen=2, tickcolor="black", showgrid=True),
            showline=True, linewidth=2, linecolor='black',
            )

        # fig.update_xaxes(title_text="Zona")
        # fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
        fig.update_layout(hovermode='y unified')
        fig.update_traces(hovertemplate = "%{y} m")
        fig.update_yaxes(autorange="reversed")
        y_max = max(self.df.iloc[:,0])
        fig.update(layout_yaxis_range = [0,y_max])
        fig.update_yaxes(rangemode="tozero")
        return fig
    
    def kapasitas_dukung_ijin(self,B,qc):
        qa = (qc/30)
        if B <= 1.2:
            pass
        else:
            qa = (qc/50) * (((B+0.3)/B)**2)
        qa = round(qa*self.kPa,2)
        return qa
    
    def solve_qa(self,Bmin=0.8,Bmax=2.0):
        Bmax = Bmax + 0.1
        list_b = np.arange(Bmin,Bmax,0.1)
        list_qc = self.df.iloc[:,1].to_list()
        list_z = self.df.iloc[:,0].to_list()
        N_data = len(list_z)

        self.df_qa = pd.DataFrame()
        self.df_qa["Kedalaman [m]"] = list_z

        for B in list_b:
            list_qa = []
            # list_qc_avg = []
            for i in range(N_data):
                z = list_z[i]
                idx_start = i
                idx_end = [idx for idx, ele in enumerate(list_z) if ele > z+B]
                if len(idx_end) == 0:
                    qc_avg = np.average(list_qc[idx_start:])
                else:
                    idx_end = idx_end[0]
                    qc_avg = np.average(list_qc[idx_start:idx_end])
                qa = self.kapasitas_dukung_ijin(B,qc_avg)

                list_qa.append(qa)
                # list_qc_avg.append(qc_avg)
            self.df_qa[f"B={round(B,2)}m, qa [kPa]"] = list_qa

    def plot(self,idx=0,size=[750,350],color="blue"):
        param = list(self.df.columns)[idx+1]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.df[param], y=self.df.iloc[:,0],name=param, line = dict(width=2, color=color), hovertemplate = 'z=%{y:.2f}m <br>nilai=%{x:.2f}',))
        fig.update_layout(height=size[0], width=size[1])
        fig.update_yaxes(title_text="Kedalaman Tanah (m)")
        fig.update_xaxes(title_text=param, showline=True, linewidth=2, linecolor='black', showgrid=True)
        fig.update_xaxes(side = "top")
        fig.update_yaxes(autorange="reversed", showline=True, linewidth=2, linecolor='black', showgrid=True)
        y_max = max(self.df.iloc[:,0])
        fig.update(layout_yaxis_range = [0,y_max])
        fig.update_yaxes(rangemode="tozero")
        return fig

    def plot_qa(self,param=None,size=[750,350]):
        fig = go.Figure()
        title = f"Kapasitas dukung pondasi lebar {param}"
        fig.update_layout(title_text=title)
        fig.add_trace(go.Scatter(x=self.df_qa[param], y=self.df_qa.iloc[:,0],name=param, line = dict(width=2)))
        fig.update_layout(height=size[0], width=size[1])
        fig.update_yaxes(title_text="Kedalaman Tanah (m)")
        fig.update_xaxes(title_text=param, showline=True, linewidth=2, linecolor='black', showgrid=True)
        # fig.update_xaxes(side = "top")
        fig.update_yaxes(autorange="reversed", showline=True, linewidth=2, linecolor='black')
        y_max = max(self.df_qa.iloc[:,0])
        fig.update(layout_yaxis_range = [0,y_max])
        fig.update_yaxes(rangemode="tozero", showgrid=True)
        return fig

    def plot_all_qa(self,size=[880,350]):
        fig = go.Figure()
        title = f"Kapasitas dukung pondasi [kPa]"
        fig.update_layout(title_text=title)
        list_lebar = list(self.df_qa.columns)[1:]
        for param in list_lebar:
            fig.add_trace(go.Scatter(x=self.df_qa[param], y=self.df_qa.iloc[:,0],name=param, line = dict(width=2)))

        fig.update_layout(height=size[0], width=size[1], legend=dict(orientation="h"))
        fig.update_yaxes(title_text="Kedalaman Tanah (m)")
        fig.update_xaxes(title_text= 'qa [kPa]', showline=True, linewidth=2, linecolor='black', showgrid=True)
        # fig.update_xaxes(side = "top")
        fig.update_yaxes(autorange="reversed", showline=True, linewidth=2, linecolor='black')
        y_max = max(self.df_qa.iloc[:,0])
        fig.update(layout_yaxis_range = [0,y_max])
        fig.update_yaxes(rangemode="tozero", showgrid=True)
        return fig   
