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
if not os.path.exists(GP):
    try: Image.new('RGBA', (1,1), (0,0,0,0)).save(GP)
    except: pass

st.title("DXFカメラ (iPhone完全対応版)")

# 2. DXF変換
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        doc, aud = recover.read(io.BytesIO(up.getvalue()))
        if aud.has_errors: aud.fix()
        fig = plt.figure(figsize=(10,10))
        ax = fig.add_axes([0,0,1,1])
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(fig)
        img = ImageOps.invert(Image.open(buf).convert('RGB'))
        alp = img.convert("L").point(lambda x: 255 if x < 128 else 0)
        img.putalpha(alp)
        img.save(GP)
        st.success("図面保存完了")
    except Exception as e: st.error(f"Error: {e}")

# 3. HTML/JS（iPhoneの画面比率を強制同期）
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

h = "<style>"
h += ".grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;width:280px;margin:auto;}"
h += ".btn{background:#eee;border:1px solid #999;padding:15px;border-radius:5px;text-align:center;cursor:pointer;font-weight:bold;}"
h += "#sht{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);width:70px;height:70px;background:rgba(255,255,255,0.4);border-radius:50%;border:5px solid #fff;z-index:10;}"
h += "</style>"
h += "<button id='st' style='width:100%;padding:20px;background:red;color:#fff;border:none;border-radius:10px;'>📸 カメラ起動</button>"
h += "<div id='ar' style='display:none;position:relative;width:100%;background:#000;overflow:hidden;margin-top:10px;border-radius:15px;'>"
h += "<video id='v' autoplay playsinline style='width:100%;'></video>"
h += "<img id='g' src='REPLACE' style='position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) scale(0.8);opacity:0.5;pointer-events:none;'>"
h += "<div id='sht'></div></div>"
h += "<div style='margin-top:20px;'><div style='display:flex;justify-content:center;gap:10px;margin-bottom:10px;'>"
h += "<div class='btn' id='zi'>➕ 拡大</div><div class='btn' id='zo'>➖ 縮小</div></div>"
h += "<div class='grid'><div></div><div class='btn' id='u'>⬆️</div><div></div>"
h += "<div class='btn' id='l'>⬅️</div><div class='btn' id='rs'>Reset</div><div class='btn' id='r'>➡️</div>"
h += "<div></div><div class='btn' id='d'>⬇️</div><div></div></div></div>"
h += "<canvas id='c' style='display:none;'></canvas><script>"
h += "let s=0.8,x=0,y=0;const g=document.getElementById('g'),v=document.getElementById('v'),ar=document.getElementById('ar'),st=document.getElementById('st');"
h += "function up(){g.style.transform='translate(calc(-50% + '+x+'px),calc(-50% + '+y+'px)) scale('+s+')';}"
h += "st.onclick=()=>{navigator.mediaDevices.getUserMedia({video:{facingMode:'environment',width:{ideal:1280}}}).then(m=>{v.srcObject=m;ar.style.display='block';st.style.display='none';});};"
h += "document.getElementById('zi').onclick=()=>{s+=0.2;up();}; document.getElementById('zo').onclick=()=>{s-=0.2;up();};"
h += "document.getElementById('u').onclick=()=>{y-=20;up();}; document.getElementById('d').onclick=()=>{y+=20;up();};"
h += "document.getElementById('l').onclick=()=>{x-=20;up();}; document.getElementById('r').onclick=()=>{x+=20;up();};"
h += "document.getElementById('rs').onclick=()=>{s=0.8;x=0;y=0;up();};"

# 【iPhone Retinaディスプレイ完全補正ロジック】
h += "document.getElementById('sht').onclick=()=>{const c=document.getElementById('c'),t=c.getContext('2d');"
h += "const vw=v.videoWidth; const vh=v.videoHeight;"
h += "c.width=vw; c.height=vh; t.drawImage(v,0,0);"
h += "if(g.src.includes('base64')){"
# iPhoneの画面上の「見えているガイドの幅」をピクセルで取得
h += "  const gRect = g.getBoundingClientRect();"
h += "  const vRect = v.getBoundingClientRect();"
# ビデオの解像度と表示サイズの比率
h += "  const ratio = vw / vRect.width;"
# 見えている通りの幅・高さを計算
h += "  const drawW = gRect.width * ratio;"
h += "  const drawH = gRect.height * ratio;"
# 見えている通りの位置（ビデオの中心からのズレ）を計算
h += "  const drawX = (vw / 2) + (x * ratio) - (drawW / 2);"
h += "  const drawY = (vh / 2) + (y * ratio) - (drawH / 2);"
h += "  t.globalAlpha=0.5; t.drawImage(g, drawX, drawY, drawW, drawH);"
h += "}"
h += "const a=document.createElement('a');a.download='result.png';a.href=c.toDataURL('image/png');a.click();};</script>"

components.html(h.replace("REPLACE", gs), height=850)
if st.button("🔄 表示を更新"): st.rerun()
