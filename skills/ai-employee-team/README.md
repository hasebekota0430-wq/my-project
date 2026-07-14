# AI社員チーム（ai-employee-team）

Codex／Claude の**個人用スキル**。1つのスキルの中に5人分の社員（ひしょこ・リサ・リブ・マテ・オーディン）の
役割と手順を保存したAIオフィス。Discordサーバーも常時稼働のPCも不要。

受付役の **ひしょこ** に依頼すると、必要な社員の役割を読み込んで仕事を進める。
**検索・閲覧・調査・下書き表示は自動**、**ファイル作成・編集・カレンダー変更・Slack/メール送信・共有変更・削除は
すべて事前確認** が固定ルール。

## 使い方

このスキルを個人用スキルとして配置し（推奨：`C:\Users\kota.hasebe\.codex\skills\ai-employee-team`）、
「ひしょこ、〇〇して」と依頼する。例：

- 「ひしょこ、過去の社内議論を調べて、役員協議用の資料を作って」
- 「ひしょこ、今週の予定と空き時間を教えて」
- 「ひしょこ、このSlackスレッドの返信案を作って」
- 「ひしょこ、このメールの返信案を作って」

## 構成

```
ai-employee-team/
├─ SKILL.md                 全体像・フロー・最重要ルール（入口）
├─ agents/
│  ├─ hishoko.md            受付・スケジュール・Slack/メール返信・承認管理
│  ├─ risa.md               外部（Web）調査・出典管理
│  ├─ ribu.md               社内横断検索（Drive/Slack/Gmail）
│  ├─ mate.md               資料作成（添付フォーマットを踏襲）
│  └─ odin.md               監査（誤字・論理・根拠・機密）
├─ references/
│  ├─ approval-rules.md     全操作の承認ルール
│  ├─ audit-checklist.md    オーディンの監査項目
│  └─ document-template.md  マテ用の資料作成ルール（体裁・構成）
└─ templates/
   └─ discussion-paper-template.md  協議・議論ペーパーの雛形
```

社員は後から追加できる（例：HR・マーケ・法務確認）。`agents/` に1ファイル足し、`SKILL.md` の名簿に追記する。
