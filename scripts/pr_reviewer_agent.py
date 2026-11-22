import os
import sys
import json
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_security_rules():
    rules = []
    rules_dir = ROOT_DIR / "security-rules"
    if rules_dir.exists():
        for p in sorted(rules_dir.rglob("*.md")):
            if p.name.startswith("_"):
                continue
            rules.append(
                f"--- ПРАВИЛО: {p.relative_to(ROOT_DIR).as_posix()} ---\n"
                f"{p.read_text(encoding='utf-8')}\n"
            )
    return "\n".join(rules)


def call_gemini(diff_text, rules_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Не задан GEMINI_API_KEY")

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    system_instruction = (
        "Ты — строгий Principal SecOps Engineer и Code Reviewer.\n"
        "Проанализируй переданный Git Diff изменений в Pull Request на основе базы правил безопасности.\n"
        "Правила ответа:\n"
        "1. Указывай только реальные уязвимости, баги безопасности или грубые ошибки.\n"
        "2. Если код чистый, так и напиши: 'Замечаний по безопасности нет'.\n"
        "3. Формат ответа: краткие маркированные списки с указанием сути проблемы и рекомендацией по исправлению.\n"
        "4. Без воды и приветствий."
    )

    user_prompt = (
        f"БАЗА ПРАВИЛ БЕЗОПАСНОСТИ:\n{rules_text}\n\n"
        f"GIT DIFF ИЗМЕНЕНИЙ В PR:\n{diff_text}"
    )

    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Нет ответа от модели")
        )


def github_api_request(url, method="GET", data=None):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-PR-Reviewer-Bot",
    }
    payload = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def main():
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")

    if not pr_number:
        print("ℹ️ Скрипт запущен вне Pull Request или переменная PR_NUMBER не передана.")
        return

    print(f"==> Запрос diff для PR #{pr_number} в репозитории {repo}...")

    diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    token = os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(
        diff_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.diff",
        },
    )

    with urllib.request.urlopen(req) as resp:
        diff_text = resp.read().decode("utf-8")

    if not diff_text.strip():
        print("ℹ️ Diff пуст, ревью не требуется.")
        return

    if len(diff_text) > 15000:
        diff_text = diff_text[:15000] + "\n... [diff обрезан из-за превышения лимита длины]"

    print("==> Загрузка базы правил безопасности...")
    rules_text = load_security_rules()

    print("==> Отправка запроса к Google Gemini...")
    review_comment = call_gemini(diff_text, rules_text)

    formatted_comment = f"🛡️ **AI Security & Code Review Assistant**\n\n{review_comment}"

    print(f"==> Публикация комментария в PR #{pr_number}...")
    comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    github_api_request(comment_url, method="POST", data={"body": formatted_comment})
    print("✅ Ревью успешно опубликовано!")


if __name__ == "__main__":
    main()
