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
GP = os.path.join(SD, "guide.png")
st.set_page_config(page_title="DXF Cam", layout="centered")
st.title("DXFカメラガイド")

# 2. DXF変換ロジック
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

# 3. HTML/JS コンポーネント (エラー防止のため極限まで短縮)
st.header("2. 撮影と調整")
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

# 1行が絶対に切れないように、短く結合します
h = "<style>"
h += ".grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:5px; width:280px; margin:auto; }"
h += ".btn { background:#eee; border:1px solid #999; padding:15px; border-radius:5px; text-align:center; cursor:pointer; font-weight:bold; }"
h += "#sht { width:65px; height:65px; background:red; border-radius:50%; border:4px solid #fff; margin:15px auto; cursor:pointer; }"
h += "</style>"

h += "<button id='st' style='width:100%; padding:20px; background:red; color:#fff; border:none; border-radius:10px; font-size:18px;'>📸 カメラ起動</button>"

h += "<div id='ar' style='display:none; position:relative; width:100%; background:#000; overflow:hidden; margin-top:10px;'>"
h += "<video id='v' autoplay playsinline style='width:100%;'></video>"
h += "<img id='g' src='REPLACE' style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%) scale(0.8); opacity:0.5; pointer-events:none;'>"
h += "</div>"

h += "<div id='box' style='margin-top:20px;'>"
h += "<div style='display:flex; justify-content:center; gap:10px; margin-bottom:10px;'>"
h += "<div class='btn' id='zi'>➕ 拡大</div><div class='btn' id='zo'>➖ 縮小</div></div>"
h += "<div class='grid'>"
h += "<div></div><div class='btn' id='u'>⬆️</div><div></div>"
h += "<div class='btn' id='l'>⬅️</div><div class='btn' id='rs'>Reset</div><div class='btn' id='r'>➡️</div>"
h += "<div></div><div class='btn' id='d'>⬇️</div><div></div></div>"
h += "<div id='sht'></div></div>"
h += "<canvas id='c' style='display:none;'></canvas>"

h += "<script>"
h += "let s=0.8, x=0, y=0;"
h += "const g=document.getElementById('g'), v=document.getElementById('v'), ar=document.getElementById('ar'), st=document.getElementById('st');"
h += "function up(){ g.style.transform='translate(calc(-50% + '+x+'px), calc(-50% + '+y+'px)) scale('+s+')'; }"
h += "st.onclick=()=>{ navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}).then(m=>{ v.srcObject=m; ar.style.display='block'; st.style.display='none'; }); };"
h += "document.getElementById('zi').onclick=()=>{ s+=0.05; up(); };"
h += "document.getElementById('zo').onclick=()=>{ s-=0.05; up(); };"
h += "document.getElementById('u').onclick=()=>{ y-=10; up(); };"
h += "document.getElementById('d').onclick=()=>{ y+=10; up(); };"
h += "document.getElementById('l').onclick=()=>{ x-=10; up(); };"
h += "document.getElementById('r').onclick=()=>{ x+=10; up(); };"
h += "document.getElementById('rs').onclick=()=>{ s=0.8; x=0; y=0; up(); };"
h += "document.getElementById('sht').onclick=()=>{ "
h += "const c=document.getElementById('c'), t=c.getContext('2d'); c.width=v.videoWidth; c.height=v.videoHeight; t.drawImage(v,0,0);"
h += "if(g.src.includes('base64')){ let dw=c.width*s, dh=g.naturalHeight*(dw/g.naturalWidth), rt=c.width/ar.offsetWidth;"
h += "t.globalAlpha=0.5; t.drawImage(g,(c.width-dw)/2+(x*rt),(c.height-dh)/2+(y*rt),dw,dh); }"
h += "const a=document.createElement('a'); a.download='pic.png'; a.href=c.toDataURL(); a.click(); };"
h += "</script>"

final_h = h.replace("REPLACE", gs)
components.html(final_h, height=850)
if st.button("🔄 表示を更新"): st.rerun()
