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

st.set_page_config(page_title="DXF-AR Cam", layout="wide")
st.title("DXF ARガイド (マーカー型)")

# 2. DXF変換ロジック
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
        # 背景を透明にする処理
        img = Image.open(buf).convert("RGBA")
        datas = img.getdata()
        new_data = []
        for item in datas:
            # 白背景（またはそれに近い色）を透明にする
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)
        img.save(GP)
        st.success("✅ AR用図面の準備完了")
    except Exception as e: st.error(f"Error: {e}")

# 3. AR.js (A-Frame) 実装
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

# AR用のHTML
h = f"""
<script src="https://aframe.io/releases/1.2.0/aframe.min.js"></script>
<script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>

<body style="margin: 0px; overflow: hidden;">
    <a-scene embedded arjs="sourceType: webcam; debugUIEnabled: false;">
        <a-marker preset="hiro">
            <a-image src="{gs}" 
                     position="0 0 0" 
                     rotation="-90 0 0" 
                     width="3" height="3"
                     opacity="0.7">
            </a-image>
        </a-marker>
        <a-entity camera></a-entity>
    </a-scene>
</body>
"""

if gs:
    st.info("💡 下のエリアにカメラが表示されます。'Hiroマーカー'をカメラにかざしてください。")
    components.html(h, height=600)
else:
    st.warning("先にDXFファイルをアップロードしてください。")

# マーカー画像の案内
with st.expander("Hiroマーカーの画像はこちら（別のスマホで表示するか印刷してください）"):
    st.image("https://ar-js-org.github.io/AR.js/data/images/hiro.png", width=200)
