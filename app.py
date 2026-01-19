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

# 保存用フォルダの作成（サーバー上に一時保存）
SAVE_DIR = "shared_assets"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

GUIDE_PATH = os.path.join(SAVE_DIR, "guide_image.png")

st.set_page_config(page_title="DXF連携カメラ", layout="centered")

# サイドバーでモード切り替え
mode = st.sidebar.radio("モード選択", ["PC：図面アップロード", "スマホ：カメラ撮影"])

# --- モード1：PCでアップロード ---
if mode == "PC：図面アップロード":
    st.title("📁 図面アップロード (PC)")
    st.write("ここでDXFをアップロードすると、スマホ側に反映されます。")
    
    uploaded_file = st.file_uploader("DXFファイルを選択", type=['dxf'])
    
    if uploaded_file is not None:
        try:
            # 1. DXF変換ロジック
            file_bytes = uploaded_file.getvalue()
            doc, auditor = recover.read(io.BytesIO(file_bytes))
            if auditor.has_errors: auditor.fix()
            
            import matplotlib.pyplot as plt
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            out = MatplotlibBackend(ax)
            Frontend(ctx, out).draw_layout(doc.modelspace())
            
            # PNG変換
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
            plt.close(fig)
            
            # 2. 透明化加工
            im = Image.open(img_buf).convert('RGB')
            im_inverted = ImageOps.invert(im)
            alpha = im_inverted.convert("L").point(lambda x: 255 if x < 128 else 0)
            im_inverted.putalpha(alpha)
            
            # 3. サーバーに保存（スマホで読み込むため）
            im_inverted.save(GUIDE_PATH)
            st.success("図面をサーバーに保存しました！スマホで「撮影モード」を開いてください。")
            st.image(im_inverted, caption="現在のガイド画像", width=300)
            
        except Exception as e:
            st.error(f"エラー: {e}")

# --- モード2：スマホで撮影 ---
else:
    st.title("📸 カメラ撮影 (スマホ)")
    
    if not os.path.exists(GUIDE_PATH):
        st.warning("まだ図面がアップロードされていません。PCでアップロードしてください。")
    else:
        st.info("PCでアップロードされた最新の図面を読み込みました。")
        
        # 保存された画像をBase64に変換
        with open(GUIDE_PATH, "rb") as f:
            img_str = base64.b64encode(f.read()).decode()

        # カメラHTML（前回のものを使用）
        camera_html = f"""
        <div style="position: relative; width: 100%; max-width: 500px; margin: auto; background: #000;">
            <video id="video" autoplay playsinline style="width: 100%;"></video>
            <img id="guide" src="data:image/png;base64,{img_str}" 
                 style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%; opacity: 0.5; pointer-events: none;">
            <div id="shutter" style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); width: 60px; height: 60px; background: #fff; border-radius: 50%; border: 5px solid #ccc; cursor: pointer;"></div>
        </div>
        <canvas id="canvas" style="display:none;"></canvas>
        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const shutter = document.getElementById('shutter');
            const guide = document.getElementById('guide');
            navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "environment" }}, audio: false }})
            .then(stream => {{ video.srcObject = stream; }})
            .catch(err => {{ alert("カメラ起動失敗"); }});
            shutter.addEventListener('click', () => {{
                const ctx = canvas.getContext('2d');
                canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const gw = canvas.width * 0.8;
                const gh = guide.naturalHeight * (gw / guide.naturalWidth);
                ctx.globalAlpha = 0.5;
                ctx.drawImage(guide, (canvas.width-gw)/2, (canvas.height-gh)/2, gw, gh);
                const link = document.createElement('a');
                link.download = 'field_photo.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            }});
        </script>
        """
        components.html(camera_html, height=600)
        
        if st.button("最新の状態に更新"):
            st.rerun()
