# Спринт 1 — отчёт

Спринт 1 реализован и проверен **до начала Спринта 2**. Все 16 Must — PASSED. Should STR-4/TEST-2/TEST-3 выполнены; Could CLI-5 не реализован.

Команда: `.\.venv\Scripts\python.exe tests/run_tests.py --report verification/sprint1.json`.

Результат: **25 PASSED, 0 FAILED, 0 ERROR, 0 SKIPPED**, 28.595 с. [Полный лог](verification/sprint1.log), [машиночитаемые результаты и SHA-256 исходников](verification/sprint1.json), [проверки по требованиям](verification/sprint1_requirements.json).

Python 3.14.0, PyCryptodome 4.3.0 (Windows ABI3 wheel), pip 25.1.1, setuptools 82.0.1, wheel 0.46.3, packaging 26.3, Git 2.51.0.windows.2. OpenSSL 3.5.3 из Git for Windows фактически проверил ECB в обоих направлениях: пустой, кратный и некратный блокам вход; PKCS#7 одинаковый. Editable install и сборка `dist/cryptocore-0.1.0-py3-none-any.whl` завершились успешно.

Реализованы устанавливаемый пакет/console entry point, строгий CLI, AES128-адаптер, собственные ECB/PKCS#7, потоковая обработка и атомарная публикация. Проверены FIPS 197 и четыре ECB-блока SP 800-38A, длины 0/1/15/16/17/31/32, чанки 1–65536, пути с пробелами/кириллицей, неверные параметры, чтение/запись, отказ fsync/replace, некорректный padding, совпадение/алиасы путей. Проверка tracemalloc: входы 256 КиБ/4 МиБ, пик менее 1 МиБ и рост менее 256 КиБ.

При подготовке тестов исправлена опечатка в hex-фикстуре до успешного запуска; дефектов продукта по итогам проверок нет. Git создан локально; удалённых подключений нет. Подтверждены C01/C02/C06/C28 в части С1. Спринты 2–3 на этой контрольной точке ещё не реализованы.

## Все Must

| ID | Реализованное поведение | Фактические тесты (полные ID в JSON) | Статус | Доказательство |
| :-- | :-- | :-- | :-- | :-- |
| S1-STR-1 | Локальный Git и правила исключения | `test_git_packaging_and_readme` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-STR-2 | README: назначение, установка/сборка, зависимости, CLI и полный цикл | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-STR-3 | pyproject.toml, editable install и сборка wheel | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CLI-1 | Установленный cryptocore.exe запускается | `test_entrypoint_and_roundtrip` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CLI-2 | Полный набор аргументов AES-128 ECB и одна операция | `test_entrypoint_and_roundtrip`, `test_missing_and_conflicting_arguments` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CLI-3 | Строгий hex-ключ ровно 16 байт | `test_invalid_values_and_future_features` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CLI-4 | Валидация аргументов, stderr и ненулевые коды | `test_invalid_values_and_future_features`, `test_missing_and_conflicting_arguments` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CRY-1 | Только AES-128, блок и ключ 16 байт | `test_fips197_known_answer`, `test_reject_invalid_keys` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CRY-2 | Crypto.Cipher.AES как одноблочный примитив; собственных раундов нет | `test_fips197_known_answer`, `test_sp800_38a_all_ecb_blocks` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CRY-3 | Собственный ECB поверх вызовов одного блока | `test_nist_file_prefix_and_decryption`, `test_all_lengths_and_chunk_boundaries` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CRY-4 | Собственный PKCS#7: полное дополнение и строгая проверка | `test_every_padding_length`, `test_invalid_padding`, `test_padding_failure_preserves_or_does_not_create_output` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-CRY-5 | Бинарные потоки, текст UTF-8 и произвольные байты | `test_entrypoint_and_roundtrip` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-IO-1 | Чтение всего входа чанками, память ограничена | `test_file_chunk_independence`, `test_bounded_memory` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-IO-2 | Запись результата и атомарная публикация | `test_entrypoint_and_roundtrip`, `test_replace_and_sync_failures_preserve_output` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-IO-3 | Ошибки файлов: stderr, код 1, сохранность результата | `test_file_errors_preserve_existing_output`, `test_read_and_write_failures`, `test_midstream_failure_preserves_output` | PASSED | [S1 JSON](verification/sprint1.json) |
| S1-TEST-1 | Полный цикл побайтово для пустых/бинарных/граничных файлов | `test_entrypoint_and_roundtrip`, `test_all_lengths_and_chunk_boundaries` | PASSED | [S1 JSON](verification/sprint1.json) |

Невыполненных Must С1 нет. Можно переходить к Спринту 2. Приложение пока не аутентифицирует шифртекст; отказ padding не является проверкой подлинности.
