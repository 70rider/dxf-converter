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
st.write("PCでアップロード、スマホで重ね合わせ撮影がこれ1つで可能です。")

# --- セクション1：アップロード (主にPC用) ---
st.header("1. 図面のアップロード")
uploaded_file = st.file_uploader("DXFファイルを選択（PC操作）", type=['dxf'])

if uploaded_file is not None:
    with st.spinner("変換中..."):
        try:
            # DXF変換
            file_bytes = uploaded_file.getvalue()
            doc, auditor = recover.read(io.BytesIO(file_bytes))
            if auditor.has_errors: auditor.fix()
            
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            out = MatplotlibBackend(ax)
            Frontend(ctx, out).draw_layout(doc.modelspace())
            
            # PNGとして一時保存
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
            plt.close(fig)
            
            # 透明化加工
            im = Image.open(img_buf).convert('RGB')
            im_inverted = ImageOps.invert(im)
            alpha = im_inverted.convert("L").point(lambda x: 255 if x < 128 else 0)
            im_inverted.putalpha(alpha)
            
            # サーバーに保存
            im_inverted.save(GUIDE_PATH)
            st.success("✅ 図面を更新しました！下のカメラボタンで撮影できます。")
            st.image(im_inverted, caption="現在のガイド画像", width=200)
            
        except Exception as e:
            st.error(f"エラー: {e}")

st.divider()

# --- セクション2：カメラ撮影 (主にスマホ用) ---
st.header("2. 重ね合わせ撮影")

if not os.path.exists(GUIDE_PATH):
    st.info("図面をアップロードすると、ここにカメラボタンが表示されます。")
else:
    # 保存された画像をBase64に変換
    with open(GUIDE_PATH, "rb") as f:
        img_str = base64.b64encode(f.read()).decode()

    st.write("👇 下のボタンを押してカメラを起動してください")
    
    # カメラHTML
    camera_html = f"""
    <div style="position: relative; width: 100%; max-width: 500px; margin: auto; border-radius: 15px; overflow: hidden; background: #000; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <video id="video" autoplay playsinline style="width: 100%; display: block;"></video>
        <img id="guide" src="data:image/png;base64,{img_str}" 
             style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%; opacity: 0.5; pointer-events: none;">
        <div id="shutter" style="position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%); width: 70px; height: 70px; background: #fff; border-radius: 50%; border: 6px solid rgba(255,255,255,0.4); cursor: pointer;"></div>
    </div>
    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const shutter = document.getElementById('shutter');
        const guide = document.getElementById('guide');

        navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "environment" }}, audio: false }})
        .then(stream => {{ video.srcObject = stream; }})
        .catch(err => {{ alert("カメラの起動に失敗しました。スマホで試してください。"); }});

        shutter.addEventListener('click', () => {{
            const ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // 映像を描画
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // ガイドを重ね
