# -*- coding: utf-8 -*-
import streamlit as st
import ezdxf
from ezdxf import recover
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from PIL import Image, ImageOps
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="DXF to 透明PNG 変換", layout="centered")

st.title("DXF to 透明PNG 変換ツール")
st.write("DXFファイルをアップロードすると、背景を透明化したPNGに変換します。")

uploaded_file = st.file_uploader("DXFファイルを選択してください", type=['dxf'])

if uploaded_file is not None:
    try:
        # 1. 読み込みロジック
        file_bytes = uploaded_file.getvalue()
        stream = io.BytesIO(file_bytes)
        
        # recoverを使用して破損ファイルを修復しつつ読み込み
        doc, auditor = recover.read(stream)
        
        if auditor.has_errors:
            auditor.fix()

        # 2. DXFから画像への描画処理
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_axes([0, 0, 1, 1])
        
        # 修正: RenderContextはdocを渡すだけで標準的な設定になります
        ctx = RenderContext(doc)
        
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace())
        
        img_buf = io.BytesIO()
        # 高解像度(300dpi)で保存
        fig.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(fig)
        
        # 3. Pillowによる画像加工
        img_buf.seek(0)
        im = Image.open(img_buf).convert('RGB')
        
        # 色を反転
        im_inverted = ImageOps.invert(im)
        
        # 透明化処理
        l_channel = im_inverted.convert("L")
        # 線（暗い部分）を不透明に、背景を透明にする
        alpha = l_channel.point(lambda x: 255 if x < 128 else 0)
        
        final_im = im_inverted.copy()
        final_im.putalpha(alpha)
        
        # 4. 結果の表示とダウンロード
        st.divider()
        st.image(final_im, caption="変換後の画像（背景透明）", use_container_width=True)
        
        out_buf = io.BytesIO()
        final_im.save(out_buf, format="PNG")
        
        st.download_button(
            label="✨ PNG画像をダウンロード",
            data=out_buf.getvalue(),
            file_name=f"{uploaded_file.name}.png",
            mime="image/png"
        )
        st.success("変換に成功しました！")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")