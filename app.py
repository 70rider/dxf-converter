# -*- coding: utf-8 -*-
import streamlit as st
import ezdxf
from ezdxf import recover
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from PIL import Image, ImageOps
import io
import matplotlib.pyplot as plt
import base64  # ← これを忘れずに追加
import streamlit.components.v1 as components  # ← これも追加

st.set_page_config(page_title="DXF to 透明PNG & カメラガイド", layout="centered")

st.title("DXFカメラガイドツール")
st.write("1. DXFをアップロードしてPNG変換 2. カメラで重ね合わせ撮影")

uploaded_file = st.file_uploader("DXFファイルを選択してください", type=['dxf'])

if uploaded_file is not None:
    try:
        # --- 1. DXF読み込み ---
        file_bytes = uploaded_file.getvalue()
        stream = io.BytesIO(file_bytes)
        doc, auditor = recover.read(stream)
        if auditor.has_errors:
            auditor.fix()

        # --- 2. DXFから画像への描画 ---
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace())
        
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(fig)
        
        # --- 3. Pillowによる画像加工 ---
        img_buf.seek(0)
        im = Image.open(img_buf).convert('RGB')
        im_inverted = ImageOps.invert(im)
        l_channel = im_inverted.convert("L")
        alpha = l_channel.point(lambda x: 255 if x < 128 else 0)
        final_im = im_inverted.copy()
        final_im.putalpha(alpha)
        
        # --- 4. 結果の表示とダウンロード ---
        st.divider()
        st.image(final_im, caption="変換後のガイド画像（背景透明）", use_container_width=True)
        
        out_buf = io.BytesIO()
        final_im.save(out_buf, format="PNG")
        st.download_button(label="PNG画像をダウンロード", data=out_buf.getvalue(), file_name=f"{uploaded_file.name}.png", mime="image/png")

        # --- 5. カメラガイド機能（HTML/JS） ---
        st.subheader("📸 実地撮影モード")
        st.info("スマホでアクセスすると、この図面をカメラに重ねて撮影できます。")

        # 画像をBase64に変換してHTMLに埋め込む
        buffered = io.BytesIO()
        final_im.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        camera_html = f"""
        <div style="position: relative; width: 100%; max-width: 500px; margin: auto; border: 2px solid #333; border-radius: 10px; overflow: hidden; background: #000;">
            <video id="video" autoplay playsinline style="width: 100%; display: block;"></video>
            <img id="guide" src="data:image/png;base64,{img_str}" 
                 style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%; opacity: 0.5; pointer-events: none;">
            <div id="shutter" style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); width: 60px; height: 60px; background: #fff; border-radius: 50%; border: 5px solid rgba(255,255,255,0.5); cursor: pointer; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>
        </div>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const shutter = document.getElementById('shutter');
            const guide = document.getElementById('guide');

            navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "environment" }}, audio: false }})
            .then(stream => {{ video.srcObject = stream; }})
            .catch(err => {{ alert("カメラの起動に失敗しました。HTTPS環境（Streamlit Cloud等）で試してください。"); }});

            shutter.addEventListener('click', () => {{
                const ctx = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                // 1. 背景（カメラ映像）を描画
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                // 2. ガイド（図面）を重ねる
                const guideWidth = canvas.width * 0.8;
                const guideHeight = guide.naturalHeight * (guideWidth / guide.naturalWidth);
                const x = (canvas.width - guideWidth) / 2;
                const y = (canvas.height - guideHeight) / 2;
                ctx.globalAlpha = 0.5;
                ctx.drawImage(guide, x, y, guideWidth, guideHeight);
                
                // 3. 保存
                const link = document.createElement('a');
                link.download = 'field_photo.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            }});
        </script>
        """
        # HTMLを表示
        components.html(camera_html, height=650)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
