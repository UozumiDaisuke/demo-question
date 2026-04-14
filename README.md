# 構造化面接 質問アップデートデモ

ES の内容を踏まえて、事前に用意された構造化面接の質問を候補者向けに個別最適化するデモ。

## 起動方法

```bash
pip install -r requirements.txt
cp .env.example .env   # .env の ANTHROPIC_API_KEY を実キーに書き換える
streamlit run app.py
```

`.env` に記載した `ANTHROPIC_API_KEY` は起動時に自動で読み込まれる（`python-dotenv`）。
環境変数で直接 `export` しても同様に動作する。

ブラウザで `http://localhost:8501` を開き、ES を貼り付けて「質問をアップデート」を押すと、
左に元の質問、右に Claude が個別最適化した質問が横並びで表示される。

質問セットは [questions.json](questions.json) を直接編集して差し替え可能。
