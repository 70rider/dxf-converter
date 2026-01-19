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

# 保存用設定
SAVE_DIR = "temp_assets"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
GUIDE_PATH = os.path.join(SAVE_DIR, "current_guide.png")

st.set_page_config(page_title="DXF Camera Tool", layout="centered")

st.title("DXFカメラガイド（調整機能付）")

# --- 1. 図面の準備 ---
uploaded_file = st.file_uploader("PCからDXFをアップロード", type=['dxf'])

if uploaded_file is not None:
    with st.spinner("変換中..."):
        try:
            file_bytes = uploaded_file.getvalue()
            doc, auditor = recover.read(io.BytesIO(file_bytes))
            if auditor.has_errors: auditor.fix()
            
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            out = MatplotlibBackend(ax)
            Frontend(ctx, out).draw_layout(doc.modelspace())
            
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
            plt.close(fig)
            
            im = Image.open(img_buf).convert('RGB')
            im_inverted = ImageOps.invert(im)
            alpha = im_inverted.convert("L").point(lambda x: 255 if x < 128 else 0)
            im_inverted.putalpha(alpha)
            
            im_inverted.save(GUIDE_PATH)
            st.success("✅ 図面を更新しました！")
        except Exception as e:
            st.error(f"変換エラー: {e}")

st.divider()

# --- 2. カメラ撮影 & 調整 UI ---
if os.path.exists(GUIDE_PATH):
    with open(GUIDE_PATH, "rb") as f:
        img_str = base64.b64encode(f.read()).decode()
    guide_src = f"data:image/png;base64,{img_str}"
else:
    guide_src = ""

camera_ui_html = f"""
<style>
    .controls {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 300px; margin: 20px auto; }}
    .btn {{ background: #f0f2f6; border: 1px solid #ccc; padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; user-select: none; }}
    .btn:active {{ background: #ddd; }}
    .zoom-controls {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 20px; }}
    #shutter {{ width: 70px; height: 70px; background: #ff4b4b; border-radius: 50%; border: 5px solid white; margin: 20px auto; cursor: pointer; }}
</style>

<div style="text-align: center;">
    <button id="start-camera" style="background: #ff4b4b; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 18px; width: 100%;">📸 カメラ起動</button>
</div>

<div id="camera-container" style="display: none; position: relative; width: 100%; max-width: 500px; margin: auto; overflow: hidden; background: #000; border-radius: 15px;">
    <video id="video" autoplay playsinline style="width: 100%; display: block;"></video>
    <img id="guide" src="{guide_src}" 
         style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(1); opacity: 0.5; pointer-events: none; transition: none;">
</div>

<div id="ui-panel" style="display: none;">
    <div class="zoom-controls">
        <button class="btn" id="zoom-in">➕ 拡大</button>
        <button class="btn" id="zoom-out">➖ 縮小</button>
    </div>
    <div class="controls">
        <div></div><button class="btn" id="up">⬆️</button><div></div>
        <button class="btn" id="left">⬅️</button><button class="btn" id="reset">Reset</button><button class="btn" id="right">➡️</button>
        <div></div><button class="btn" id="down">⬇️</button><div></div>
    </div>
    <div id="shutter"></div>
    <p style="text-align:center; color:#666;">図面を動かして位置を合わせてください</p>
</div>

<canvas id="canvas" style="display:none;"></canvas>

<script>
    let scale = 0.8;
    let offsetX = 0;
    let offsetY = 0;

    const guide = document.getElementById('guide');
    const container = document.getElementById('camera-container');
    const uiPanel = document.getElementById('ui-panel');
    const video = document.getElementById('video');

    function updateTransform() {{
        guide.style.transform = `translate(calc(-50% + ${{offsetX}}px), calc(-50% + ${{offsetY}}px)) scale(${{scale}})`;
    }}

    document.getElementById('start-camera').addEventListener('click', () => {{
        navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "environment" }}, audio: false }})
        .then(stream => {{
            video.srcObject = stream;
            container.style.display = 'block';
            uiPanel.style.display = 'block';
            document.getElementById('start-camera').style.display = 'none';
        }});
    }});

    // 移動・サイズ変更イベント
    document.getElementById('zoom-in').onclick = () => {{ scale += 0.05; updateTransform(); }};
    document.getElementById('zoom-out').onclick = () => {{ scale -= 0.05; updateTransform(); }};
    document.getElementById('up').onclick = () => {{ offsetY -= 10; updateTransform(); }};
    document.getElementById('down').onclick = () => {{ offsetY += 10; updateTransform(); }};
    document.getElementById('left').onclick = () => {{ offsetX -= 10; updateTransform(); }};
    document.getElementById('right').onclick = () => {{ offsetX += 10; updateTransform(); }};
    document.getElementById('reset').onclick = () => {{ scale = 0.8; offsetX = 0; offsetY = 0; updateTransform(); }};

    document.getElementById('shutter').onclick = () => {{
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width =
