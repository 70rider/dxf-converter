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
st.title("🏗️ DXF マーカーAR (透過精度向上版)")

# 2. DXF変換 (高度な透明化処理)
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        doc, aud = recover.read(io.BytesIO(up.getvalue()))
        if aud.has_errors: aud.fix()
        fig = plt.figure(figsize=(12,12)) # 解像度を少し上げる
        ax = fig.add_axes([0,0,1,1])
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
        # --- 画像加工：輝度ベースの透明化 ---
        img = Image.open(buf).convert("RGB")
        # 1. 白黒反転（線を白くする）
        img = ImageOps.invert(img)
        
        # 2. グレースケール化して「マスク（型）」を作る
        mask = img.convert("L") 
        
        # 3. アルファチャンネルとしてマスクを適用
        # 線（白い部分）は不透明、背景（黒い部分）は透明になる
        rgba_img = img.convert("RGBA")
        rgba_img.putalpha(mask)
        
        # 4. 保存（念のため背景をクリーンアップ）
        rgba_img.save(GP)
        st.success("✅ 図面の透過処理を完了しました")
    except Exception as e: st.error(f"Error: {e}")

# 3. AR.js 実装
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

if gs:
    ar_html = f"""
    <script src="https://aframe.io/releases/1.2.0/aframe.min.js"></script>
    <script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>
    
    <div style="position: fixed; top: 10px; left: 10px; z-index: 1000; display: flex; gap: 10px;">
        <button id="btn-in" style="padding: 15px; font-size: 18px; border-radius: 8px; background: white; border: 2px solid #333;">➕ 拡大</button>
        <button id="btn-out" style="padding: 15px; font-size: 18px; border-radius: 8px; background: white; border: 2px solid #333;">➖ 縮小</button>
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
                         width="4" height="4"
                         transparent="true"
                         alpha-test="0.5">
                </a-image>
            </a-marker>
            <a-entity camera></a-entity>
        </a-scene>

        <script>
            let currentScale = 1.0;
            const target = document.getElementById('target-img');
            document.getElementById('btn-in').onclick = () => {{
                currentScale *= 1.2;
                target.setAttribute('scale', `${{currentScale}} ${{currentScale}} ${{currentScale}}`);
            }};
            document.getElementById('btn-out').onclick = () => {{
                currentScale /= 1.2;
                target.setAttribute('scale', `${{currentScale}} ${{currentScale}} ${{currentScale}}`);
            }};
        </script>
    </body>
    """
    components.html(ar_html, height=700)
    st.image("https://ar-js-org.github.io/AR.js/data/images/hiro.png", width=150, caption="このマーカーを映してください")
