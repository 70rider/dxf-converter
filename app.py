# -*- coding: utf-8 -*-
import streamlit as st
import ezdxf
from ezdxf import recover
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from PIL import Image, ImageOps
import io, os, base64
import streamlit.components.v1 as components
import matplotlib.pyplot as plt

# 1. 準備
SD = "temp_assets"
if not os.path.exists(SD): os.makedirs(SD)
GP = os.path.join(SD, "guide.png")
if not os.path.exists(GP):
    try: Image.new('RGBA', (1,1), (0,0,0,0)).save(GP)
    except: pass

st.title("DXFカメラツール")

# 2. 変換
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        doc, aud = recover.read(io.BytesIO(up.getvalue()))
        if aud.has_errors: aud.fix()
        fig = plt.figure(figsize=(10,10))
        ax = fig.add_axes([0,0,1,1])
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(fig)
        img = ImageOps.invert(Image.open(buf).convert('RGB'))
        alp = img.convert("L").point(lambda x: 255 if x < 128 else 0)
        img.putalpha(alp)
        img.save(GP)
        st.success("図面保存完了")
    except Exception as e: st.error(f"Error: {e}")

# 3. HTML (1行を短く分割)
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

h = "<style>"
h += ".grid{display:grid;grid-template-columns:1fr 1fr 1fr;"
h += "gap:5px;width:280px;margin:auto;}"
h += ".btn{background:#eee;border:1px solid #999;padding:15px;"
h += "border-radius:5px;text-align:center;cursor:pointer;"
h += "font-weight:bold;}"
h += "#sht{position:absolute;bottom:20px;left:50%;"
h += "transform:translateX(-50%);width:70px;height:70px;"
h += "background:rgba(255,255,255,0.4);border-radius:50%;"
h += "border:5px solid #fff;z-index:10;}"
h += "</style>"
h += "<button id='st' style='width:100%;padding:20px;"
h += "background:red;color:#fff;border:none;"
h += "border-radius:10px;'>📸 カメラ起動</button>"
h
