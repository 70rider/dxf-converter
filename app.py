# -*- coding: utf-8 -*-
import streamlit as st
import ezdxf
from ezdxf import recover
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from PIL import Image, ImageOps
import io
import os
import base64
import streamlit.components.v1 as components
import matplotlib.pyplot as plt

# --- 1. 準備 ---
S_DIR = "temp_assets"
if not os.path.exists(S_DIR):
    os.makedirs(S_DIR)
G_PATH = os.path.join(S_DIR, "current_guide.png")

st.set_page_config(page_title="DXF Cam", layout="centered")
st.title("DXFカメラガイド（位置調整付）")

# --- 2. アップロード ---
st.header("1. 図面の準備")
up_file = st.file_uploader("DXFを選択", type=['dxf'])

if up_file is not None:
    try:
        f_bytes = up_file.getvalue()
        doc, aud = recover.read(io.BytesIO(f_bytes))
        if aud.has_errors: aud.fix()
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace())
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(fig)
        im = Image.open(buf).convert('RGB')
        inv = ImageOps.invert(im)
        alp = inv.convert("L").point(lambda x: 255 if x < 128 else 0)
        inv.putalpha(alp)
        inv.save(G_PATH)
        st.success("✅ 図面を更新しました")
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()

# --- 3. カメラ (HTML組み立て) ---
st.header("2. 現場撮影")

g_src = ""
if os.path.exists(G_PATH):
    with open(G_PATH, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    g_src = "data:image/png;base64," + b64

# 1行を短くしてエラーを回避
h = ""
h += "<style>"
h += ".controls { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 20px auto; max-width: 300px; }"
h += ".btn { background: #eee; border: 1px solid #ccc; padding: 15px; border-radius: 8px; text-align: center; cursor: pointer; font-weight: bold; }"
h += ".z-box { display: flex; justify-content: center; gap: 20px; margin: 10px; }"
h += "#shutter { width: 70px; height: 70px; background: red; border-radius: 50%; border: 4px solid #fff; margin: 20px auto; }"
h += "</style>"

h += "<button id='start' style='width:100%; padding:15px; background:red; color:white; border:none; border-radius:10px; font-size:18px;'>📸 カメラ起動</button>"

h += "<div id='cam-area' style='display:none; position:relative; width:100%; overflow:hidden; background:#000; border-radius:15px; margin-top:10px;'>"
h += "  <video id='v' autoplay playsinline style='width:100%;'></video>"
h += "  <img id='g' src='REPLACE_ME' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%) scale(0.8); opacity:0.5; pointer-events:none;'>"
h += "</div>"

h += "<div id='ui' style='display:none;'>"
h += "  <div class='z-box'>"
