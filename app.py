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
GP = os.path.join(SD, "guide_ar.png")

st.set_page_config(page_title="DXF-AR", layout="wide")
st.title("🏗️ DXF AR (アスペクト比・完全同期版)")

# セッション状態の初期化
if 'ar_ratio' not in st.session_state:
    st.session_state.ar_ratio = 1.0

# 2. DXF変換
up = st.file_uploader("DXFを選択", type=['dxf'])
if up:
    try:
        doc, aud = recover.read(io.BytesIO(up.getvalue()))
        if aud.has_errors: aud.fix()
        
        # 描画（余白を最小限にする設定）
        fig = plt.figure(figsize=(15, 15))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off() # 軸を完全に消す
        
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace())
        
        # 一旦メモリ上に保存して画像サイズを確認
        buf = io.BytesIO()
        # bbox_inches='tight' ではなく、余白を含めて出力されるのを前提に処理
        fig.savefig(buf, format='png', transparent=True)
        plt.close(fig)
        
        # --- 画像加工と比率計算 ---
        img = Image.open(buf).convert("RGBA")
        
        # 1. 実際の図面が描かれている範囲をクロップ（余白カット）
        # これにより、画像そのものの比率が「図面そのものの比率」になります
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        
        # 2. 画像のピクセルサイズからアスペクト比を計算
        w_px, h_px = img.size
        st.session_state.ar_ratio = h_px / w_px
        
        # 3. 反転と透過処理
        # 元がRGBAなので一度RGBにして反転、再度マスクを作る
        rgb_part = img.convert("RGB")
        inv_img = ImageOps.invert(rgb_part)
        
        # 輝度をマスクにして透過
        mask = inv_img.convert("L")
        final_img = inv_img.convert("RGBA")
        final_img.putalpha(mask)
        
        final_img.save(GP)
        st.success(f"✅ 比率計算完了: 横 1.00 に対して 縦 {st.session_state.ar_ratio:.2f}")
        
    except Exception as e:
        st.error(f"Error: {e}")

# 3. AR表示 (計算した比率を適用)
gs = ""
if os.path.exists(GP):
    with open(GP, "rb") as f:
        gs = "data:image/png;base64," + base64.b64encode(f.read()).decode()

if gs:
    # 横幅を基準(例: 5m分)にして、縦幅を比率で決める
    base_w = 5.0
    calc_h = base_w * st.session_state.ar_ratio

    ar_html = f"""
    <script src="https://aframe.io/releases/1.2.0/aframe.min.js"></script>
    <script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>
    <div style="position: fixed; top: 10px; left: 10px; z-index: 1000; display: flex; gap: 10px;">
        <button id="btn-in" style="padding: 15px; font-size: 18px; border-radius: 8px; background: white;">➕ 拡大</button>
        <button id="btn-out" style="padding: 15px; font-size: 18px; border-radius: 8px; background: white;">➖ 縮小</button>
    </div>
    <body style="margin: 0; overflow: hidden;">
        <a-scene embedded vr-mode-ui="enabled: false" arjs="sourceType: webcam; debugUIEnabled: false;">
            <a-assets><img id="layer" src="{gs}"></a-assets>
            <a-marker preset="hiro">
                <a-image id="target-img"
                         src="#layer" 
                         position="0 0 0" 
                         rotation="-90 0 0" 
                         width="{base_w}" height="{calc_h}"
                         material="transparent: true; alphaTest: 0.2; shader: flat; side: double;">
                </a-image>
            </a-marker>
            <a-entity camera></a-entity>
        </a-scene>
        <script>
            let scale = 1.0;
            const target = document.getElementById('target-img');
            document.getElementById('btn-in').onclick = () => {{ scale *= 1.1; target.setAttribute('scale', `${{scale}} ${{scale}} ${{scale}}`); }};
            document.getElementById('btn-out').onclick = () => {{ scale /= 1.1; target.setAttribute('scale', `${{scale}} ${{scale}} ${{scale}}`); }};
        </script>
    </body>
    """
    components.html(ar_html, height=700)
