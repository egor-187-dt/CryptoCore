# Проверки Спринтов 1–3 и официальный NIST STS

Дата актуализации: 2026-11-09. **57/57 Must — PASSED; S3-TEST-3 закрыт реальным запуском NIST STS 2.1.2. Спринт 4 не начинался.**

## Регрессия

```powershell
.\.venv\Scripts\python.exe tests/run_tests.py --report verification/local.json
```

Последний фактический запуск: **62 PASSED, 0 FAILED, 0 ERROR, 0 SKIPPED**, 86.109 с. [JSON](verification/nist_sts_regression.json), [лог](verification/nist_sts_regression.log). Код 0 — полный успех; 1 — failures/errors; 2 — обязательная внешняя проверка пропущена. OpenSSL используется реальным subprocess; путь задаётся OPENSSL_EXE или определяется через PATH/Git for Windows.

Набор проверяет AES KAT, собственные пять режимов, PKCS#7, бинарный полный цикл, CLI, OpenSSL в обоих направлениях, RNG, атомарность файлов и память. tracemalloc измеряет Python-аллокации, не полный RSS. `NISTSTSAvailabilityTests.test_official_nist_sts_all_15` теперь валидирует реальные результаты STS и их происхождение: это не имитация статистических тестов и не новый запуск STS при каждом unittest.

## S3-TEST-3 — PASSED

Все **15 тестов, 188 подтестов** выполнены официальным STS. Выборка: 100 000 000 байт, 800 × 1 000 000 бит, binary MSB-first. SHA-256: `5faab330d7ba576a3fcd6dc67d6f86ba0bbe1c8b4cd25a3dd2bcfcd62ff91c6e`. Источник — функция CSPRNG проекта, без изменения алгоритмов.

Основной прогон четырьмя процессами: 306.343 с; пилот 1.398 с, контроль data.e 1.356 с. Windows sleep guard был успешно установлен и снят. Все пропорции и P_T прошли; у Excursions/Variant 496 применимых потоков и 304 неприменимых, не засчитанных успешными. Отдельные p<0.01 сохранены и интерпретированы по NIST.

- [Полный отчёт, параметры, ограничения и команды повторения](NIST_STS_REPORT.md).
- [Предварительно зафиксированный протокол](verification/nist_sts_protocol.json).
- [Все p-values/маски применимости и статусы](verification/nist_sts_results.json).
- [188 отдельных сводок](verification/nist_sts_subtests.csv).
- [Сырые отчёты/диалоги/логи](verification/nist_sts_raw_reports.zip).
- [Объединённый штатный отчёт NIST](verification/nist_sts_finalAnalysisReport.txt).
- [Сверка официального Zig](verification/nist_sts_toolchain.json), [сборка оригинального STS](verification/nist_sts_build.json), [калибровка](verification/nist_sts_calibration.json), [время и ресурсы](verification/nist_sts_execution.json).

Фактически использован один уже сохранённый файл `artifacts/nist_sts_20261109/random.bin`; данные не подбирались повторно. Новая генерация допускается только как отдельный заранее спланированный эксперимент с отдельными путями/metadata, а не ради улучшения результата. Для воспроизведения текущих чисел нужен сохранённый бинарный файл с указанным хешем.

## Сборка и повторение STS

Компилятор, оригинальные исходники, exe, кэши и скрипты находятся внутри `artifacts/`; его нужно переносить отдельно от Git. Системный PATH, реестр, WSL и глобальные пакеты не менялись. Официальный C-код собрался без патчей. Штатные функции NIST используются и для объединения результатов; Python только управляет запуском и проверяет/суммирует реальные выходные файлы.

Скрипты bootstrap.py, build.py, run.py pilot/calibration/full, build_aggregate.py и analyze.py и порядок действий описаны в [разделе 10 отчёта](NIST_STS_REPORT.md#10-повторный-запуск). Они не перезаписывают существующие каталоги запусков. Перед повторением архивировать старые результаты и сохранить random.bin. analyze.py требует ручного обзора перед сменой итогового статуса. Случайность статистическими тестами не сертифицируется.

## Исторические данные

`verification/nist_availability.json`, `nist_data.json`, `stage1_nist_recheck.json`, sprint1/sprint2/sprint3 и stage1_final относятся к проверкам 2026-11-06; их BLOCKED/SKIPPED отражают тогдашнюю среду. Это не текущий статус. Старые выборки 12 500 000 байт не изменялись.

Smoke-проверки 1000 ключей/IV и веса Хэмминга остаются отдельными тестами и не заменяют официальный STS. Для случайных p-values и уникальности результат каждого запуска фиксируется в JSON регрессии.
