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
st.title("🏗️ DXF AR (アスペクト比修正版)")

# セッション状態で比率を保持
if 'aspect_ratio' not in st.session_state:
    st.session_state.aspect_ratio = 1.0

# 2. DXF変換
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        doc, aud = recover.read(io.BytesIO(up.getvalue()))
        if aud.has_errors: aud.fix()
        fig = plt.figure(figsize=(12,12))
        ax = fig.add_axes([0,0,1,1])
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
        
        # 図面範囲から比率を計算
        msp = doc.modelspace()
        bbox = ezdxf.bbox.extents(msp)
        dx = bbox.width
        dy = bbox.height
        if dx > 0 and dy > 0:
            st.session_state.aspect_ratio = dy / dx # 縦/横 の比率
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
        # 加工処理
        img = Image.open(buf).convert("RGB")
        img = ImageOps.invert(img)
        mask = img.convert("L")
        rgba_img = img.convert("RGBA")
        rgba_img.putalpha(mask)
        rgba_img.save(GP)
        st.success(f"✅ 変換完了 (比率: {st.session_state.aspect_ratio:.2f})")
    except Exception as e: st.error(f"Error: {e}")

# 3. HTML/JS (比率を反映)
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

if gs:
    # AR上でのサイズ計算（横幅を4とした時の縦幅を比率で出す）
    ar_w = 4.0
    ar_h = ar_w * st.session_state.aspect_ratio

    ar_html = f"""
    <script src="https://aframe.io/releases/1.2.0/aframe.min.js"></script>
    <script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>
    
    <div style="position: fixed; top: 10px; left: 10px; z-index: 1000; display: flex; gap: 10px;">
        <button id="btn-in" style="padding: 15px; font-size: 18px; border-radius: 8px; background: white; border: 2px solid #333;">➕ 拡大</button>
        <button id="btn-out" style="padding: 15px; font-size: 18px; border-radius: 8px; background: white; border: 2px solid #333;">➖ 縮小</button>
    </div>

    <body style="margin: 0; overflow: hidden;">
        <a-scene embedded vr-mode-ui="enabled: false" arjs="sourceType: webcam; debugUIEnabled: false;">
            <a-assets><img id="layer" src="{gs}"></a-assets>
            <a-marker preset="hiro">
                <a-image id="target-img"
                         src="#layer" 
                         position="0 0 0" 
                         rotation="-90 0 0" 
                         width="{ar_w}" height="{ar_h}"
                         material="transparent: true; alphaTest: 0.1; shader: flat;">
                </a-image>
            </a-marker>
            <a-entity camera></a-entity>
        </a-scene>
        <script>
            let currentScale = 1.0;
            const target = document.getElementById('target-img');
            document.getElementById('btn-in').onclick = () => {{ currentScale *= 1.2; target.setAttribute('scale', `${{currentScale}} ${{currentScale}} ${{currentScale}}`); }};
            document.getElementById('btn-out').onclick = () => {{ currentScale /= 1.2; target.setAttribute('scale', `${{currentScale}} ${{currentScale}} ${{currentScale}}`); }};
        </script>
    </body>
    """
    components.html(ar_html, height=700)
    st.image("https://ar-js-org.github.io/AR.js/data/images/hiro.png", width=150)
