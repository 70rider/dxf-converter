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

# --- 1. フォルダとパスの設定 ---
SD = "temp_assets"
if not os.path.exists(SD):
    os.makedirs(SD)
GP = os.path.join(SD, "guide.png")

st.set_page_config(page_title="DXF Camera", layout="centered")
st.title("DXFカメラガイド")

# --- 2. 図面アップロード (PC) ---
st.header("1. 図面の準備")
up = st.file_uploader("DXFをアップロード", type=['dxf'])

if up is not None:
    try:
        b = up.getvalue()
        d, a = recover.read(io.BytesIO(b))
        if a.has_errors: a.fix()
        f = plt.figure(figsize=(10, 10))
        ax = f.add_axes([0, 0, 1, 1])
        c = RenderContext(d)
        o = MatplotlibBackend(ax)
        Frontend(c, o).draw_layout(d.modelspace())
        buf = io.BytesIO()
        f.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(f)
        img = Image.open(buf).convert('RGB')
        inv = ImageOps.invert(img)
        alp = inv.convert("L").point(lambda x: 255 if x < 128 else 0)
        inv.putalpha(alp)
        inv.save(GP)
        st.success("✅ 図面を保存しました")
    except Exception as e:
        st.error(f"変換エラー: {e}")

st.divider()

# --- 3. カメラとボタンの構築 ---
st.header("2. 撮影と調整")

gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    gs = "data:image/png;base64," + encoded

# HTMLを短く分割して組み立て（コピーミス防止）
h = []
h.append("<style>")
h.append(".grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px; width: 280px; margin: 10px auto; }")
h.append(".btn { background: #eee; border: 1px solid #999; padding: 15px; border-radius: 5px; text-align: center; cursor: pointer; font-weight: bold; }")
h.append(".z-row { display: flex; justify-content: center; gap: 10px; margin: 10px; }")
h.append("#shutter { width: 60px; height: 60px; background: red; border-radius: 50%; border: 4px solid white; margin: 15px auto; cursor: pointer; }")
h.append("</style>")

# カメラ起動ボタン
h.append("<button id='start' style='width:100%; padding:20px; background:red; color:white; border:none; border-radius:10px; font-size:18px; cursor:pointer;'>📸 カメラを起動する</button>")

# カメラ表示エリア
h.append("<div id='area' style='display:none; position:relative; width:100%; background:#000; border-radius:10px; margin-top:10px; overflow:hidden;'>")
h.append("<video id='v' autoplay playsinline style='width:100%;'></video>")
h.append("<img id='g' src='REPLACE_ME' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%) scale(0.8); opacity:0.5; pointer-events:none;'>")
h.append("</div>")

# 調整ボタンパネル
h.append("<div id='ui' style='margin-top:20px;'>")
h.append("<div class='z-row'><div class='btn' id='zi'>➕ 拡大</div><div class='btn' id='zo'>➖ 縮小</div></div>")
h.append("<div class='grid'>")
h.append("<div></div><div class='btn' id='u'>⬆️</div><div></div>")
h.append("<div class='btn' id='l'>⬅️</div><div class='btn' id='rs'>Reset</div><div class='btn' id='r'>➡️</div>")
h.append("<div></div><div class='btn' id='d'>⬇️</div><div></div>")
h.append("</div>")
h.append("<div id='shutter'></div>")
h.append("</div>")

h.append("<canvas id='c' style='display:none;'></canvas>")

# JavaScript
h.append("<script>")
h.append("let s=0.8, x=0, y=0;")
h.append("const g=document.getElementById('g'), v=document.getElementById('v'), area=document.getElementById('area'), ui=document.getElementById('ui'), start=document.getElementById('start');")
h.append("function up(){ g.style.transform='translate(calc(-50% + '+x+'px), calc(-50% + '+y+'px)) scale('+s+')'; }")
h.append("start.onclick=()=>{")
h.append(" navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'},audio:false})")
h.append(" .then(stream=>{ v.srcObject=stream; area.style.display='block'; start.style.display='none'; })")
h.append(" .catch(e=>{ alert('カメラエラー: '+e.message); });")
h.append("};")
h.append("document.getElementById('zi').onclick=()=>{ s+=0.05; up(); };")
h.append("document.getElementById('zo').onclick=()=>{ s-=0.05; up(); };")
h.append("document.getElementById('u').onclick=()=>{ y-=10; up(); };")
h.append("document.getElementById('d').onclick=()=>{ y+=10; up(); };")
h.append("document.getElementById('l').onclick=()=>{ x-=10; up(); };")
h.append("document.getElementById('r').onclick=()=>{ x+=10; up(); };
