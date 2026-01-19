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

st.title("DXFカメラガイドツール")

# --- セクション1：図面のアップロード ---
st.header("1. 図面の準備")
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

# --- セクション2：カメラ起動ボタン ---
st.header("2. 現場撮影")

# ガイド画像データの準備
if os.path.exists(GUIDE_PATH):
    with open(GUIDE_PATH, "rb") as f:
        img_str = base64.b64encode(f.read()).decode()
    guide_src = f"data:image/png;base64,{img_str}"
else:
    # 図面がない場合のダミー透過画像
    guide_src = ""

# カメラ起動を制御するボタン（StreamlitのボタンではなくHTML内のボタンで完結させます）
camera_ui_html = f"""
<div style="text-align: center; margin-bottom: 20px;">
    <button id="start-camera" style="background-color: #ff4b4b; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; width: 100%;">
        📸 カメラを起動して撮影する
    </button>
</div>

<div id="camera-container" style="display: none; position: relative; width: 100%; max-width: 500px; margin: auto; border-radius: 15px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline style="width: 100%; display: block;"></video>
    <img id="guide" src="{guide_src}" 
         style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%; opacity: 0.5; pointer-events: none;">
    <div id="shutter" style="position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%); width: 70px; height: 70px; background: #fff; border-radius: 50%; border: 6px solid rgba(255,255,255,0.4); cursor: pointer;"></div>
</div>

<canvas id="canvas" style="display:none;"></canvas>

<script>
    const startBtn = document.getElementById('start-camera');
    const container = document.getElementById('camera-container');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const shutter = document.getElementById('shutter');
    const guide = document.getElementById('guide');

    startBtn.addEventListener('click', () => {{
        navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "environment" }}, audio: false }})
        .then(stream => {{
            video.srcObject = stream;
            container.style.display = 'block';
            startBtn.style.display = 'none'; // 起動後はボタンを隠す
        }})
        .catch(err => {{
            alert("カメラを起動できません。ブラウザの権限設定を確認してください。");
        }});
    }});

    shutter.addEventListener('click', () => {{
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        if (guide.src && guide.src.includes('base64')) {{
            const gw = canvas.width * 0.8;
            const gh = guide.naturalHeight * (gw / guide.naturalWidth);
            ctx.globalAlpha = 0.5;
            ctx.drawImage(guide, (canvas.width - gw) / 2, (canvas.height - gh) / 2, gw, gh);
        }}
        
        const link = document.createElement('a');
        link.download = 'capture_' + Date.now() + '.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    }});
</script>
"""

components.html(camera_ui_html, height=700)

if st.button("🔄 ページを最新に更新"):
    st.rerun()
