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

st.title("DXFカメラツール")

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

# 3. HTML (合成計算を「画面座標系」から「カメラ座標系」へ変換)
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

h = "<style>"
h += ".grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;width:280px;margin:auto;}"
h += ".btn{background:#eee;border:1px solid #999;padding:15px;border-radius:5px;text-align:center;cursor:pointer;font-weight:bold;}"
h += "#sht{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);width:75px;height:75px;background:rgba(255,255,255,0.4);border-radius:50%;border:5px solid #fff;z-index:10;}"
h += "</style>"
h += "<button id='st' style='width:100%;padding:20px;background:red;color:#fff;border:none;border-radius:10px;'>📸 カメラ起動</button>"
h += "<div id='ar' style='display:none;position:relative;width:100%;background:#000;overflow:hidden;margin-top:10px;border-radius:15px;'>"
h += "<video id='v' autoplay playsinline style='width:100%;'></video>"
h += "<img id='g' src='REPLACE' style='position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) scale(0.8);opacity:0.5;pointer-events:none;'>"
h += "<div id='sht'></div></div>"
h += "<div style='margin-top:20px;'><div style='display:flex;justify-content:center;gap:10px;margin-bottom:10px;'><div class='btn' id='zi'>➕ 拡大</div><div class='btn' id='zo'>➖ 縮小</div></div>"
h += "<div class='grid'><div></div><div class='btn' id='u'>⬆️</div><div></div><div class='btn' id='l'>⬅️</div><div class='btn' id='rs'>Reset</div><div class='btn' id='r'>➡️</div><div></div><div class='btn' id='d'>⬇️</div><div></div></div></div>"
h += "<canvas id='c' style='display:none;'></canvas><script>"
h += "let s=0.8,x=0,y=0;const g=document.getElementById('g'),v=document.getElementById('v'),ar=document.getElementById('ar'),st=document.getElementById('st');"
h += "function up(){g.style.transform='translate(calc(-50% + '+x+'px),calc(-50% + '+y+'px)) scale('+s+')';}"
h += "st.onclick=()=>{navigator.mediaDevices.getUserMedia({video:{facingMode:'environment',width:{ideal:1920}}}).then(m=>{v.srcObject=m;ar.style.display='block';st.style.display='none';});};"
h += "document.getElementById('zi').onclick=()=>{s+=0.1;up();}; document.getElementById('zo').onclick=()=>{s-=0.1;up();};"
h += "document.getElementById('u').onclick=()=>{y-=15;up();}; document.getElementById('d').onclick=()=>{y+=15;up();};"
h += "document.getElementById('l').onclick=()=>{x-=15;up();}; document.getElementById('r').onclick=()=>{x+=15;up();};"
h += "document.getElementById('rs').onclick=()=>{s=0.8;x=0;y=0;up();};"

# 【重要】撮影・合成ロジック
h += "document.getElementById('sht').onclick=()=>{const c=document.getElementById('c'),t=c.getContext('2d');"
h += "c.width=v.videoWidth;c.height=v.videoHeight;t.drawImage(v,0,0);"
h += "if(g.src.includes('base64')){"
# 1. 画面上の表示倍率（画面幅に対するカメラ解像度の比）を算出
h += "let ratio = v.videoWidth / ar.offsetWidth;"
# 2. ガイド画像の元のサイズを取得
h += "let nw = g.naturalWidth; let nh = g.naturalHeight;"
# 3. 保存時の描画サイズを計算（基本サイズ × 拡大率s × 比率ratio）
# ※ 画面上で「scale(0.8)」が基準なので、それを考慮
h += "let drawW = (ar.offsetWidth * s) * ratio;"
h += "let drawH = nh * (drawW / nw);"
# 4. 中心座標を計算（移動分x, yを比率で補正）
h += "let offX = (c.width / 2) + (x * ratio) - (drawW / 2);"
h += "let offY = (c.height / 2) + (y * ratio) - (drawH / 2);"
h += "t.globalAlpha=0.5; t.drawImage(g, offX, offY, drawW, drawH);}"
h += "const a=document.createElement('a');a.download='pic.png';a.href=c.toDataURL('image/png');a.click();};</script>"

components.html(h.replace("REPLACE", gs), height=850)
if st.button("🔄 表示を更新"): st.rerun()
