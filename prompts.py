from __future__ import annotations

import json

SYSTEM_PROMPT = """あなたは構造化面接の設計を支援するアシスタントです。
与えられた「元の質問」を、候補者のエントリーシート（ES）の内容を踏まえて、その候補者向けに具体化・深掘りした質問文に書き換えてください。

各質問には評価観点（クライテリア / サブクライテリア / 評価ポイント / 質問種別）が付与されます。書き換える際はこの評価意図を絶対に維持してください。

厳守事項:
- 質問が測定しようとしている評価観点を変えない（観点のズレは絶対 NG）。
- ES に書かれた具体的なエピソード・固有名詞・数値・役割・期間などを質問文に自然に織り込み、候補者が答えやすく、面接官が深掘りしやすい形にする。
- ES に該当するエピソードがない質問は、元の質問文をそのまま `updated_question` として返す（情報を捏造しない）。
- 導入質問（intro）はエピソード全体に踏み込む形、深掘り質問（deep）は ES のエピソードを前提にその中の具体的行動・判断を問う形にする。
- 質問は 1〜2 文、敬体（です・ます調）で統一。
- 出力は指定 JSON のみ。前置き・後置き・マークダウンのコードフェンスは付けない。

出力スキーマ（厳守）:
{
  "updated": [
    {"id": "<入力と同じID>", "updated_question": "…", "rationale": "ES のどの記述を踏まえたかを日本語で1文"},
    ...
  ]
}
入力の全ての質問に対して、同じ id で返すこと。"""


def _flatten(questions_data: dict) -> list[dict]:
    rows = []
    for c in questions_data["criteria"]:
        for sc in c["subcriteria"]:
            for q in sc["intro_questions"]:
                rows.append({
                    "id": q["id"],
                    "criteria": c["name"],
                    "subcriteria": sc["name"],
                    "evaluation": sc["evaluation"],
                    "type": "intro",
                    "question": q["question"],
                })
            for q in sc["deep_questions"]:
                rows.append({
                    "id": q["id"],
                    "criteria": c["name"],
                    "subcriteria": sc["name"],
                    "evaluation": sc["evaluation"],
                    "type": "deep",
                    "question": q["question"],
                })
    return rows


def build_user_prompt(es_text: str, questions_data: dict) -> str:
    payload = {
        "entry_sheet": es_text,
        "questions": _flatten(questions_data),
    }
    return (
        "以下のエントリーシートと質問セットを踏まえて、指定の JSON スキーマで全件を返してください。\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
