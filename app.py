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
GP = os.path.join(SD, "guide_ar.png")

st.set_page_config(page_title="DXF-AR", layout="wide")
st.title("🏗️ DXF マーカーAR (サイズ調整機能付)")

# 2. DXF変換 (白黒反転 ＋ 透明化)
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        doc, aud = recover.read(io.BytesIO(up.getvalue()))
        if aud.has_errors: aud.fix()
        fig = plt.figure(figsize=(10,10))
        ax = fig.add_axes([0,0,1,1])
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
        img = Image.open(buf).convert("RGB")
        inv_img = ImageOps.invert(img)
        rgba_img = inv_img.convert("RGBA")
        datas = rgba_img.getdata()
        new_data = []
        for item in datas:
            if item[0] < 50 and item[1] < 50 and item[2] < 50:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        rgba_img.putdata(new_data)
        rgba_img.save(GP)
        st.success("✅ AR図面の準備完了")
    except Exception as e: st.error(f"Error: {e}")

# 3. AR.js + UI操作の実装
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

if gs:
    ar_html = f"""
    <script src="https://aframe.io/releases/1.2.0/aframe.min.js"></script>
    <script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>
    
    <div style="position: fixed; top: 10px; left: 10px; z-index: 1000; display: flex; gap: 10px;">
        <button id="btn-in" style="padding: 15px; font-size: 20px; border-radius: 10px; background: white;">➕ 拡大</button>
        <button id="btn-out" style="padding: 15px; font-size: 20px; border-radius: 10px; background: white;">➖ 縮小</button>
        <button id="btn-reset" style="padding: 15px; font-size: 20px; border-radius: 10px; background: white;">🔄 Reset</button>
    </div>

    <body style="margin: 0; overflow: hidden;">
        <a-scene embedded vr-mode-ui="enabled: false" arjs="sourceType: webcam; debugUIEnabled: false;">
            <a-assets>
                <img id="layer" src="{gs}">
            </a-assets>
            <a-marker preset="hiro">
                <a-image id="target-img"
                         src="#layer" 
                         position="0 0 0" 
                         rotation="-90 0 0" 
                         width="2" height="2"
                         transparent="true">
                </a-image>
            </a-marker>
            <a-entity camera></a-entity>
        </a-scene>

        <script>
            let currentScale = 1.0;
            const target = document.getElementById('target-img');
            
            document.getElementById('btn-in').onclick = () => {{
                currentScale += 0.2;
                target.setAttribute('scale', `${{currentScale}} ${{currentScale}} ${{currentScale}}`);
            }};
            
            document.getElementById('btn-out').onclick = () => {{
                if (currentScale > 0.2) currentScale -= 0.2;
                target.setAttribute('scale', `${{currentScale}} ${{currentScale}} ${{currentScale}}`);
            }};

            document.getElementById('btn-reset').onclick = () => {{
                currentScale = 1.0;
                target.setAttribute('scale', '1 1 1');
            }};
        </script>
    </body>
    """
    components.html(ar_html, height=700)
    
    with st.expander("👉 Hiroマーカー"):
        st.image("https://ar-js-org.github.io/AR.js/data/images/hiro.png", width=200)
else:
    st.write("DXFをアップロードしてください。")
