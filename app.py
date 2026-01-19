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

# --- 1. 準備設定 ---
SAVE_DIR = "temp_assets"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
GUIDE_PATH = os.path.join(SAVE_DIR, "current_guide.png")

st.set_page_config(page_title="DXF Camera Tool", layout="centered")
st.title("DXFカメラガイド（調整機能付）")

# --- 2. 図面アップロード ---
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

# --- 3. カメラ撮影 & 調整 ---
st.header("2. 現場撮影")

guide_src = ""
if os.path.exists(GUIDE_PATH):
    with open(GUIDE_PATH, "rb") as f:
        img_str = base64.b64encode(f.read()).decode()
    guide_src = "data:image/png;base64," + img_str

# 三重引用符を避け、配列を結合する方法でHTMLを作成（エラー防止）
html_parts = [
    "<style>",
    "  .controls { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 300px; margin: 20px auto; }",
    "  .btn { background: #f0f2f6; border: 1px solid #ccc; padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; user-select: none; text-align: center; }",
    "  .btn:active { background: #ddd; }",
    "  .zoom-controls { display: flex; justify-content: center; gap: 20px; margin-bottom: 20px; }",
    "  #shutter { width: 70px; height: 70px; background: #ff4b4b; border-radius: 50%; border: 5px solid white; margin: 20px auto; cursor: pointer; }",
    "</style>",
    "<div style='text-align: center;'>",
    "  <button id='start-camera' style='background: #ff4b4b; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 18px; width: 100%; cursor: pointer;'>📸 カメラ起動</button>",
    "</div>",
    "<div id='camera-container' style='display: none; position: relative; width: 100%; max-width: 500px; margin: auto; overflow: hidden; background: #000; border-radius
