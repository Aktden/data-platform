# Домашнее задание 4

**ФИО:** Актанов Денис Юрьевич  
**Группа:** 24/11/1  
**Дата оформления:** 28.10.2026

## Сводная таблица планов

Замеры выполнены на MongoDB 7.0.14 с исходными 1200 событиями `logs.events`. Стадии перечислены в порядке выполнения, снизу вверх по дереву плана. Полные документы `explain("executionStats")` сохранены в шести JSON-файлах.

| Файл | Индекс | Возвращено | Документов прочитано | Ключей прочитано | Стадии |
|---|---|---:|---:|---:|---|
| [plan-1.json](plan-1.json) | Нет | 33 | 1200 | 0 | COLLSCAN → SORT |
| [plan-2.json](plan-2.json) | service, level, ts, duration_ms | 33 | 33 | 43 | IXSCAN → FETCH |
| [plan-3a.json](plan-3a.json) | duration_ms, service, level, ts | 33 | 33 | 378 | IXSCAN → SORT → FETCH |
| [plan-3b.json](plan-3b.json) | service, level, duration_ms, ts | 33 | 33 | 33 | IXSCAN → SORT → FETCH |
| [plan-4-bez.json](plan-4-bez.json) | Нет | 10 | 1200 | 0 | COLLSCAN → SORT |
| [plan-4.json](plan-4.json) | level, duration_ms | 10 | 10 | 10 | IXSCAN → FETCH → LIMIT |

## Задача 1 Без индекса

```js
db.events.find({
  service: "payments",
  level: "error",
  duration_ms: { $gt: 500 }
}).sort({ ts: -1 })
```

Запрос возвращает 33 события. Подходящего индекса нет, поэтому сервер проверяет все 1200 документов через `COLLSCAN`, после чего сортирует найденные события по `ts` в памяти. Полезная доля чтения — `33 / 1200 × 100 = 2,75%`.

[Разбор плана без индекса](https://dfrancour.dev/tools/mongodb-paste-the-plan#v1:zZTbbtNAEIbfZdVLg-KGpCF3oQeBCKTEFRKqEBq8k3TpHtzddZoQ-d2ZWTeHQgtSkRBXcWbmn8M3Y68FLisNyn5EH5SzYihykYmbGv3qXIO16MVwLSwYDBWUSH7t5uE5LtDGQJHKSlyeKR3RFxjFcAY6YCYq8AHlB07D-gOwUgwv10KTUCcL3lAu9N550TTZWgT0C8UFNr4KViYVSW5Ze4jU4BcTUsicavU6nab53Ny1-xrCFclOBof90dmrAfVGg9ljKK_wLa7uewws33DjKCe-cLrmzGGKHCu3M-yCRlb-LqoowYYLd0okncSfA26VtcrOmSZ3HiLMGWMxmV5QJ8H5eA6R8CUvjTt8ltNIBs1YGUVT5p0Xg95Rv9PJRFxVLA3KVBoT_KqORZtwl_l4Mh4Xx6P3FDBLi_kHG5DKYxnbA5o5fwteskp4_EZ2lDw9yS45loiWiSV1HlOunaUuSwxki74mdHaKsfaWYXa7e8ILZfCd0lpRJGNxETTtOJwuwagUvrGeuHLPmh8yxf36cwwPLOXPdU9DVAYipkq3zl8Hzt7tZQLkAmy5kVpEyapUO2__f1Ko2xYDLJAhsJtZhej8noHKTM7S019dSQsCIhTqOxaUiZt7mQ8ob00v6YkK19tjDRWN11JNj-RmIfVFgFifXP_P3T11U7yLRzeV94-evKmHXgSy_nKGDb8dpTMm8VkTMf4V2-_qjuAWz45LtqF5hzF7HFJ7O_eO5kB-vfuMC_rnaPl58wM)


## Задача 2 Индекс по ESR

E — точное равенство по `service` и `level`; S — сортировка `ts: -1`; R — диапазон `duration_ms > 500`.

```js
db.events.createIndex({ service: 1, level: 1, ts: -1, duration_ms: 1 })
```

Возвращено 33 документа, прочитано 33 документа и 43 ключа. Чтение документов уменьшилось в `1200 / 33 ≈ 36,36` раза, или на 97,25%. Отдельная стадия `SORT` исчезла: внутри выбранных значений `service` и `level` записи индекса уже идут в нужном порядке по `ts`. Разница между 43 ключами и 33 результатами связана с проверкой границ диапазона `duration_ms`, расположенного после поля сортировки; в фактическом плане есть 10 поисков `seeks`.

[Разбор плана с индексом ESR](https://dfrancour.dev/tools/mongodb-paste-the-plan#v1:7VVLTxsxEP4ryOLQw4KSABXkFkIiUBWgJK1aBRSZ9SQYvPZie0NQtP-9M95HNrSl11bqyet5fjPzeWfNYJUqLvVXsE4azbqszSL2nIF9vVZca7Csu2aaJ-BSHgPqlVm4fViC9g4tpRawGkrlwY7Bs-6cKwcRS7l1ID5TGPLf5Vqw7nTNFDqqIIFnjAXWGsvyPFozB3YpKUGlS_lrEpIEtcgs9whwlrhgssBcR61Wnt_lJdxz7h7Q7ey487E3PD1GbFiY7vP4AT4BomBHg6PO4eFJBzUJX10QcBBXdmxURpHdDZCtqGvYGPW0eM9qHHPtJmaAnTQC3hq8SK2lXlA3CbnzfEFtHA4m_fPQwDTz40K40V58G_d7l6h-gtdr7rG7hXPVpHZUtRK_sEfdPTy3etTOy-Fc4uwwYuk6a8-CI57ezfbas4bTjEYv3ShTXoaWVSWWAgTy4LZgTO9qHPRJQOjcAjKlCUn3RUscUx1TunHgSENwza2XXG0khL7mZQfDSguxL1g6N_aFW1Ex8NRkWrzBxqa3NYluWbTTvN2xBnIyDEwsrMrPYBIqYtMRX2H90c5IajyDZrtG9gHJGO1IPd9voTpHzjILjwgXBE2-6gOyKQ48won7gHcjyeIYHMq8zbB6fQM-s5qIdHDQcJzIBEZSKYmWLQRoPFeIyQ1WPJHB_PCgFJ-ZuCHeihII537Fxz_nHTgvE-4h5H8x9skVOblYch1XjhpAkA_rnhSX7xKUCD6OL4HqLyJYcN7YhgAzXA0DscVPBXBlgQt661f3j4X1--_nbyrn_1v-J99yGNyb9-UAiCftFjmnboJDh4INdD2zJk3DPfwIYpMkYQGu2VzSyer1OQ-bc6vWzeKrqyr3ZPT7LYiIjPUkKwiEgl1xX25rhjfzRDT6AQ)


## Задача 3 Порядок полей

Вариант А:

```js
db.events.createIndex({ duration_ms: 1, service: 1, level: 1, ts: -1 })
```

Прочитано 378 ключей: ведущий диапазон по длительности охватывает записи разных сервисов и уровней. Несмотря на покрытие всех полей условия индексом, готового порядка по `ts` нет, поэтому сервер выполняет `SORT`.

Вариант Б:

```js
db.events.createIndex({ service: 1, level: 1, duration_ms: 1, ts: -1 })
```

Прочитано только 33 ключа, но стадия `SORT` остаётся. Индекс упорядочен сначала по `duration_ms` и только затем по `ts`, поэтому весь диапазон не отсортирован по времени. Для этой задачи выбираю ESR: он читает немного больше ключей, зато сразу обеспечивает нужный порядок и не требует отдельной сортировки результата. На небольших данных разница во времени может быть незаметной; выбор стоит пересматривать по фактической нагрузке, селективности и ограничениям сортировки.

## Задача 4 Десять самых долгих ошибок

```js
db.events.find({ level: "error" }).sort({ duration_ms: -1 }).limit(10)
db.events.createIndex({ level: 1, duration_ms: -1 })
```

E — `level`, S — `duration_ms: -1`, диапазона нет. Без индекса прочитано 1200 документов, с индексом — 10 ключей и 10 документов, возвращено 10. Хотя ошибок в коллекции 180, сервер читает индекс от самых долгих событий и останавливается после первых десяти благодаря `LIMIT`.

[Разбор плана второго запроса с индексом](https://dfrancour.dev/tools/mongodb-paste-the-plan#v1:7VVNTxsxEP0ryOIYqiyX0txCPkTUBigJVasQRcN6Egxee7G9EITy3zvjTTbb0FL149BDT2uP3_g9v5m1nwUucw3KfELnlTWiJRLREPcFuqdzDcagE61nYSBDn0OKtK7twr_BBzTBE1IZicu-0gHdCINozUF7bIgcnEf5kbfhfE14zYN9vKct0DnrxGq1JjoBf0PRw_a7o-PmUZd2JUmmA-kNvkfKF_1ucthpvuWVDJYDpkR55kZWF4FE-wtkrKzYt6C2ka-hRikYP7Y98sBK3AU8KmOUWbAPrN0HWLABHwbDwZikaJWp0M5sYejcSZO9yIswKlFbeL837pyIH60OPo867VNavsOncwhko6kZljSELByw_FnmResgWa0tP6WKcDEYN0tmNdTsgCuo_LDQQUX_NuddB4jmxtdIJtMdlsmUWfylUVSeKl35UaxqLXAOLijQ2wgrqzrpkLZVDtNQ9tXcukdwctMzx-Sb_EaGmFyVnXElGnvVcCpeyBOTISzpII29oTL0Jchqxd3k8JboUHLFNuegLkhj_cn6EPm2kSJN0VMsuILUmwsMhTPcAFzNCjZWGQ6V1oqQFA82gCZW31tCpip4DHdtuhOu0y_Qf6-Pfs7b80FlEDDyP1p3R_sk1BsgH8Ckm0SDKDknonjyRaGWcebhAfn85ZpDH6yrBYjhrB-77Rd7-jelN_-6dBrJF96DdgiSr5ez69sS_fo_-C8d5_998Ef3QTRwpx88YqwX5-d-TN5jWRSedp3N8zgv75LUZhkYyYLmir-ievPm8bmrSd08aERhXeCFl1WKf1apY19er99RTrF3FF19BQ)


## Ответы для приёмки

- `totalKeysExamined` считает просмотренные записи индекса, а `totalDocsExamined` — прочитанные документы коллекции. Это разные действия, поэтому числа могут различаться.
- `FETCH` получает полные документы по ссылкам из индекса. Запрос возвращает все поля, а четырёх полей составного индекса для этого недостаточно.
- При вставке события сервер записывает документ и соответствующую запись в каждый применимый индекс. При изменении индексируемого поля индекс тоже обновляется.
- Каждый индекс занимает место и увеличивает стоимость записи. Индексы выбирают под реальные фильтры, сортировки и частоту запросов.
- Сортировка имеет ограничения памяти и может использовать диск при разрешённых настройках; наличие `SORT` само по себе не означает неизбежную ошибку на любой большой коллекции.

## Воспроизведение

```bash
python -m pip install -r requirements.txt
python lesson_04/plan.py --all
```

Команды выполняются из корня проекта на учебной базе. Режим `--all` удаляет неслужебные индексы только `logs.events` между замерами и сохраняет шесть планов заново. Числа также находятся в [measurements.json](measurements.json).

Три ссылки созданы кнопкой Paste the Plan и проверены открытием. В копиях планов для ссылок удалены служебные `serverInfo` и `serverParameters`; исходные JSON в папке сохранены полностью. Показатели и дерево выполнения в ссылках совпадают с исходными файлами. Дополнительная сверка выполнена с исходными `executionStats`; результат MongoPilot в отчёт не включён.
