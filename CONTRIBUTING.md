# Как добавлять правила безопасности

1. Создайте новый `.md`-файл в директории `security-rules/` (имя файла в `kebab-case`, например `xss-dom.md`).
2. Добавьте в начало файла YAML frontmatter с полями `id`, `title` и `severity`.
3. Опишите признаки уязвимости, на которые должен обращать внимание агент, и способ remediation.
4. Запустите локально `python scripts/build_index.py`, чтобы проверить валидацию и обновить `security-rules/_index.md`.
5. Откройте Pull Request с изменениями.
