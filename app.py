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

st.set_page_config(page_title="DXF-AR Precision 3%", layout="wide")
st.title("🏗️ DXF AR (調整量3%)")

if 'ar_ratio' not in st.session_state:
    st.session_state.ar_ratio = 1.0

# 2. DXF変換
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        doc, aud = recover.read(io.BytesIO(up.getvalue()))
        if aud.has_errors: aud.fix()
        fig = plt.figure(figsize=(15, 15))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', transparent=True)
        plt.close(fig)
        
        img = Image.open(buf).convert("RGBA")
        bbox = img.getbbox()
        if bbox: img = img.crop(bbox)
        
        w_px, h_px = img.size
        st.session_state.ar_ratio = h_px / w_px
        
        rgb_part = img.convert("RGB")
        inv_img = ImageOps.invert(rgb_part)
        mask = inv_img.convert("L")
        final_img = inv_img.convert("RGBA")
        final_img.putalpha(mask)
        final_img.save(GP)
        st.success(f"✅ 図面変換完了")
    except Exception as e:
        st.error(f"Error: {e}")

# 3. AR表示
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

if gs:
    base_w = 5.0
    calc_h = base_w * st.session_state.ar_ratio

    ar_html = f"""
    <script src="https://aframe.io/releases/1.2.0/aframe.min.js"></script>
    <script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>
    
    <style>
        .ui {{ position: fixed; top: 10px; left: 10px; z-index: 1000; display: flex; flex-direction: column; gap: 8px; }}
        .row {{ display: flex; gap: 10px; align-items: center; }}
        .lbl {{ color: white; background: rgba(0,0,0,0.6); padding: 5px 10px; border-radius: 5px; font-size: 14px; min-width: 40px; text-align: center; }}
        button {{ padding: 15px; font-size: 18px; border-radius: 10px; background: white; border: 2px solid #333; min-width: 60px; font-weight: bold; }}
        button:active {{ background: #ccc; }}
    </style>

    <div class="ui">
        <div class="row">
            <div class="lbl">全体</div>
            <button id="all-in">＋</button>
            <button id="all-out">－</button>
        </div>
        <div class="row">
            <div class="lbl">横幅</div>
            <button id="w-in">＋</button>
            <button id="w-out">－</button>
        </div>
    </div>

    <body style="margin: 0; overflow: hidden;">
        <a-scene embedded vr-mode-ui="enabled: false" arjs="sourceType: webcam; debugUIEnabled: false;">
            <a-assets><img id="layer" src="{gs}"></a-assets>
            <a-marker preset="hiro">
                <a-image id="target-img" src="#layer" position="0 0 0" rotation="-90 0 0" 
                         width="{base_w}" height="{calc_h}" material="transparent: true; alphaTest: 0.2; shader: flat;">
                </a-image>
            </a-marker>
            <a-entity camera></a-entity>
        </a-scene>
        
        <script>
            let scX = 1.0, scY = 1.0;
            const target = document.getElementById('target-img');
            const step = 1.03; // 3%ずつの調整

            const up = () => {{
                target.setAttribute('scale', `${{scX}} ${{scY}} 1`);
            }};

            document.getElementById('all-in').onclick = () => {{ scX *= step; scY *= step; up(); }};
            document.getElementById('all-out').onclick = () => {{ scX /= step; scY /= step; up(); }};
            document.getElementById('w-in').onclick = () => {{ scX *= step; up(); }};
            document.getElementById('w-out').onclick = () => {{ scX /= step; up(); }};
        </script>
    </body>
    """
    components.html(ar_html, height=750)
