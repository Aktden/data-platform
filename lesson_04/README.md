# Отчёт по плану запроса и индексам

Запрос 1: `{ service: "payments", level: "error", duration_ms: { $gt: 500 } }`, сортировка `{ ts: -1 }`.

| План | Индекс | nReturned | totalDocsExamined | totalKeysExamined | Шаги |
|---|---|---:|---:|---:|---|
| plan-1.json | только `_id_` | 33 | 1200 | 0 | COLLSCAN → SORT |
| plan-2.json | `{service:1, level:1, ts:-1, duration_ms:1}` | 33 | 33 | 43 | IXSCAN → FETCH |
| plan-3a.json | `{duration_ms:1, service:1, level:1, ts:-1}` | 33 | 33 | 378 | IXSCAN → FETCH → SORT |
| plan-3b.json | `{service:1, level:1, duration_ms:1, ts:-1}` | 33 | 33 | меньше, но с SORT | IXSCAN → FETCH → SORT |
| plan-4-bez.json | без индекса | 10 | 1200 | 0 | COLLSCAN → LIMIT |
| plan-4.json | индекс по ESR для запроса 2 | 10 | 10 | 10 | IXSCAN → FETCH → LIMIT |

Правило ESR: сначала равенства (`service`, `level`), затем сортировка (`ts`), затем диапазон (`duration_ms`). `SORT` исчезает, потому что индекс уже выдаёт документы в порядке `ts`. `totalKeysExamined` — просмотренные записи индекса; `totalDocsExamined` — реально прочитанные документы; `FETCH` нужен для чтения полей документа после нахождения ссылок в индексе. Индекс по всем полям подряд не ставят: он занимает место, замедляет записи и не обязан улучшать каждый запрос.

В эту папку положите реальные JSON, экспортированные через Compass/mongosh, заменив учебные строки в таблице фактическими числами.
