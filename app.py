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

st.set_page_config(page_title="DXF-AR Precision", layout="wide")
st.title("🏗️ DXF AR (超精密調整モード)")

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
        .ui {{ position: fixed; top: 10px; left: 10px; z-index: 1000; display: flex; flex-direction: column; gap: 5px; font-family: sans-serif; }}
        .row {{ display: flex; gap: 5px; align-items: center; }}
        .grp-lbl {{ font-size: 10px; color: white; background: rgba(0,0,0,0.5); padding: 2px 5px; border-radius: 3px; width: 40px; text-align: center; }}
        button {{ padding: 10px; font-size: 14px; border-radius: 5px; background: white; border: 1px solid #333; min-width: 45px; cursor: pointer; }}
        button:active {{ background: #ddd; }}
        .btn-main {{ background: #ffff00; font-weight: bold; }}
        .btn-sub {{ background: #e3f2fd; }}
    </style>

    <div class="ui">
        <div class="row"><span class="grp-lbl">全体</span>
            <button class="btn-main" id="all-in">＋</button><button class="btn-main" id="all-out">－</button>
        </div>
        <div class="row"><span class="grp-lbl">横幅</span>
            <button class="btn-sub" id="w-in">＋</button><button class="btn-sub" id="w-out">－</button>
        </div>
        <div class="row"><span class="grp-lbl">縦幅</span>
            <button class="btn-sub" id="h-in">＋</button><button class="btn-sub" id="h-out">－</button>
        </div>
        <div class="row"><span class="grp-lbl">回転</span>
            <button id="r-left">↺</button><button id="r-right">↻</button>
        </div>
        <button id="reset" style="margin-top:5px; background: #ffcccc;">リセット</button>
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
            let scX = 1.0, scY = 1.0, rot = 0;
            const target = document.getElementById('target-img');
            const step = 1.01; // 1%ずつの変化
            const rotStep = 0.5; // 0.5度ずつの回転

            const up = () => {{
                target.setAttribute('scale', `${{scX}} ${{scY}} 1`);
                target.setAttribute('rotation', `-90 0 ${{rot}}`);
            }};

            document.getElementById('all-in').onclick = () => {{ scX *= step; scY *= step; up(); }};
            document.getElementById('all-out').onclick = () => {{ scX /= step; scY /= step; up(); }};
            document.getElementById('w-in').onclick = () => {{ scX *= step; up(); }};
            document.getElementById('w-out').onclick = () => {{ scX /= step; up(); }};
            document.getElementById('h-in').onclick = () => {{ scY *= step; up(); }};
            document.getElementById('h-out').onclick = () => {{ scY /= step; up(); }};
            document.getElementById('r-left').onclick = () => {{ rot -= rotStep; up(); }};
            document.getElementById('r-right').onclick = () => {{ rot += rotStep; up(); }};
            document.getElementById('reset').onclick = () => {{ scX = 1.0; scY = 1.0; rot = 0; up(); }};
        </script>
    </body>
    """
    components.html(ar_html, height=750)
