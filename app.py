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

# --- 1. 準備 ---
SD = "temp_assets"
if not os.path.exists(SD): os.makedirs(SD)
GP = os.path.join(SD, "guide.png")
if not os.path.exists(GP):
    try: Image.new('RGBA', (1, 1), (0,0,0,0)).save(GP)
    except: pass

st.set_page_config(page_title="DXF Cam", layout="centered")
st.title("DXFカメラガイド")

# --- 2. DXF変換 ---
st.header("1. 図面の準備")
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        b = up.getvalue()
        d, a = recover.read(io.BytesIO(b))
        if a.has_errors: a.fix()
        f = plt.figure(figsize=(10,10))
        ax = f.add_axes([0,0,1,1])
        Frontend(RenderContext(d), MatplotlibBackend(ax)).draw_layout(d.modelspace())
        buf = io.BytesIO()
        f.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(f)
        img = ImageOps.invert(Image.open(buf).convert('RGB'))
        alp = img.convert("L").point(lambda x: 255 if x < 128 else 0)
        img.putalpha(alp)
        img.save(GP)
        st.success("✅ 保存完了")
    except Exception as e: st.error(f"Error: {e}")

st.divider()

# --- 3. カメラと調整 (HTMLリスト方式でエラーを完全回避) ---
st.header("2. 撮影と調整")
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

# 1行ずつリストに入れて、最後に結合する（SyntaxError対策）
L = [
    "<style>",
    ".grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:5px; width:280px; margin:auto; }",
    ".btn { background:#eee; border:1px solid #999; padding:15px; border-radius:5px; text-align:center; cursor:pointer; font-weight:bold; }",
    "#sht { position:absolute; bottom:20px; left:50%; transform:translateX(-50%); width:75px; height:75px; background:rgba(255,255,255,0.4); border-radius:50%; border:5px solid rgba(255,255,255,0.7); cursor:pointer; z-index:10; box-shadow:0 0 10px rgba(0,0,0,0.5); }",
    "</style>",
    "<button id='st' style='width:100%; padding:20px; background:red; color:#fff; border:none; border-radius:10px; font-size:18px;'>📸 カメラ起動</button>",
    "<div id='ar' style='display:none; position:relative; width:100%; background:#000; overflow:hidden; margin-top:10px; border-radius:15px;'>",
    "<video id='v' autoplay playsinline style='width:100%;'></video>",
    "<img id='g' src='REPLACE' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%) scale(0.8); opacity:0.5; pointer-events:none;'>",
    "<div id='sht'></div>",
    "</div>",
    "<div id='box' style='margin-top:20px;'>",
    "<div style='display:flex; justify-content:center; gap:10px; margin-bottom:10px;'>",
    "<div class='btn' id='zi'>➕ 拡大</div><div class='btn' id='zo'>➖ 縮小</div></div>",
    "<div class='grid'>",
    "<div></div><div class='btn' id='u'>⬆️</div><div></div>",
    "<div class='btn' id='l'>⬅️</div><div class='btn' id='rs'>Reset</div><div class='btn' id='r'>➡️</div>",
