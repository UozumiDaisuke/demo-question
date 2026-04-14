from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from es_presets import ES_PRESETS
from prompts import SYSTEM_PROMPT, build_user_prompt

load_dotenv(Path(__file__).parent / ".env")

MODEL = "claude-sonnet-4-6"
QUESTIONS_PATH = Path(__file__).parent / "questions.json"


@st.cache_data
def load_questions() -> dict:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


def update_questions(es_text: str, questions_data: dict) -> dict[str, dict]:
    from anthropic import Anthropic

    client = Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(es_text, questions_data)}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    data = json.loads(text)
    return {item["id"]: item for item in data["updated"]}


def render_row(original_q: dict, updated: dict | None) -> None:
    left, right = st.columns(2)
    with left:
        st.write(original_q["question"])
    with right:
        if updated and original_q["id"] in updated:
            item = updated[original_q["id"]]
            st.write(item.get("updated_question", original_q["question"]))
            rationale = item.get("rationale")
            if rationale:
                with st.expander("どこを踏まえたか"):
                    st.write(rationale)
        else:
            st.write("—（未アップデート）")


def main() -> None:
    st.set_page_config(page_title="構造化面接 質問アップデートデモ", layout="wide")
    st.title("構造化面接 質問アップデートデモ")
    st.caption("ES の内容を踏まえて、事前に用意された質問文を候補者向けに個別最適化します。")

    data = load_questions()
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not has_api_key:
        st.warning("環境変数 `ANTHROPIC_API_KEY` が設定されていません。`.env` もしくは環境変数で設定してください。")

    st.subheader("エントリーシート")

    def _apply_preset() -> None:
        st.session_state["es_text"] = ES_PRESETS[st.session_state["es_preset"]]

    st.selectbox(
        "サンプルESを選ぶ",
        options=list(ES_PRESETS.keys()),
        key="es_preset",
        on_change=_apply_preset,
    )
    es_text = st.text_area(
        "候補者の学生時代のエピソードなどを貼り付けてください",
        height=250,
        placeholder="例: 私は大学で約30名のテニスサークルの副代表を務め、練習参加率が50%まで落ちていた課題に対して…",
        key="es_text",
    )

    if st.button("質問をアップデート", type="primary", disabled=not has_api_key):
        if not es_text.strip():
            st.error("ES を入力してください。")
        else:
            with st.spinner("Claude がアップデート中…"):
                try:
                    st.session_state["updated"] = update_questions(es_text, data)
                except json.JSONDecodeError as e:
                    st.session_state["updated"] = None
                    st.error(f"Claude の返答を JSON として解釈できませんでした: {e}")
                except Exception as e:
                    st.session_state["updated"] = None
                    st.error(f"API 呼び出しでエラーが発生しました: {e}")

    st.divider()
    updated = st.session_state.get("updated")

    for c in data["criteria"]:
        st.header(f"クライテリア：{c['name']}")
        st.caption(c["description"])

        for sc in c["subcriteria"]:
            st.subheader(f"{sc['id']} {sc['name']}")
            st.markdown(f"**何を評価するか：** {sc['evaluation']}")

            h_left, h_right = st.columns(2)
            h_left.markdown("**元の質問**")
            h_right.markdown("**ES を踏まえた質問**")

            st.markdown("**導入質問**（いずれか1問を使用）")
            for q in sc["intro_questions"]:
                render_row(q, updated)

            st.markdown("**深掘り質問**（回答を踏まえて2〜3問を選択）")
            for q in sc["deep_questions"]:
                render_row(q, updated)

            st.markdown("---")


if __name__ == "__main__":
    main()
