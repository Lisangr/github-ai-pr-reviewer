import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "security-rules"


def main():
    print("==> Валидация базы правил безопасности...")
    rules = []
    if not RULES_DIR.exists():
        print("Ошибка: папка security-rules не найдена!")
        sys.exit(1)

    for p in sorted(RULES_DIR.rglob("*.md")):
        if p.name.startswith("_"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        content = p.read_text(encoding="utf-8")
        if "---" not in content:
            print(f"Ошибка: в файле {rel} отсутствует frontmatter.")
            sys.exit(1)
        rules.append(rel)

    index_path = RULES_DIR / "_index.md"
    lines = [
        "<!-- Автоматически сгенерированный файл. Не править руками. -->",
        "# Индекс правил безопасности (Security Rules Index)",
        "",
        "| Правило | Путь |",
        "|---|---|",
    ]
    for r in rules:
        name = pathlib.Path(r).stem.replace("-", " ").capitalize()
        lines.append(f"| {name} | [{r}]({pathlib.Path(r).name}) |")

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: Успешно проиндексировано правил: {len(rules)}")


if __name__ == "__main__":
    main()
