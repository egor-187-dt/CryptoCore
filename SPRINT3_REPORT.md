# Спринт 3 — отчёт

С3 реализован после успешного С2. **21 из 22 Must — PASSED; S3-TEST-3 — BLOCKED. Полная приёмка С3 не заявляется.** Should CLI-5 и TEST-4 выполнены. Бонусов и функциональности С4 нет.

Команда: `.\.venv\Scripts\python.exe tests/run_tests.py --report verification/sprint3.json`.

Результат: **57 тестов: 56 PASSED, 0 FAILED, 0 ERROR, 1 SKIPPED**, 143.802 с. Пропуск — официальный NIST STS. Runner намеренно возвращает 2 для неполного набора обязательных проверок. [Лог](verification/sprint3.log), [результаты, метрики, версии и SHA-256](verification/sprint3.json), [ID требований/тестов](verification/sprint3_requirements.json).

Реализованы отдельный csprng.py поверх os.urandom, валидация счётчика байтов, понятные ошибки RNG, автоматический 16-байтный AES-ключ, немедленный однократный вывод hex, обязательный ключ при decrypt и общий источник всех IV. Проверена точная сериализация, исключающая добавление ключа в файл. При явном ключе поведение сохранено, слабые повторяющиеся/последовательные ключи вызывают stderr-предупреждение без изменения ключа. Тест обязательности encryption-key С1 адаптирован к запланированному изменению E01; его историческая проверка сохранена в SPRINT1_REPORT.

Регрессия С1/С2 и OpenSSL 3.5.3 для всех пяти режимов прошла. Python 3.14.0, PyCryptodome 4.3.0. Инъекции отказа ключевого/IV RNG сохраняют output; если ключ уже сгенерирован до отказа IV, он напечатан только один раз, повторного вывода нет.

## Фактическая статистика

- Уникальных ключей из 1000: 1000.
- Уникальных IV из 1000: 1000.
- Доля единичных битов в независимой выборке 128000 бит: 0.50136719 (smoke-критерий 0.48–0.52).

Эти проверки не заменяют NIST STS и не доказывают стойкость источника.

## Блокировка STS

`assess 1000000` фактически попытались запустить: FileNotFoundError/WinError 2. Исполняемый STS, C-компилятор и make в проверенных местах отсутствуют; WSL не установлен. [Результаты проверки среды](verification/nist_availability.json). Глобальная конфигурация Windows не менялась.

Подготовлена реальная выборка CSPRNG: **12 500 000 байт**, 100 последовательностей по 1 000 000 бит; [размер и SHA-256](verification/nist_data.json). p-values и результаты 15 тестов отсутствуют. [TESTING.md](TESTING.md) описывает сборку/запуск официального пакета в подготовленной среде, бинарный ввод, все 15 тестов, анализ применимости/долей и необходимые сырые отчёты. До этого S3-TEST-3 остаётся BLOCKED, а переход к С4 не считается полностью подготовленным.

## Все Must

| ID | Реализованное поведение | Фактические тесты (полные ID в JSON) | Статус | Доказательство |
| :-- | :-- | :-- | :-- | :-- |
| S3-STR-1 | Упаковка/структура С1-С2 сохранены; прежние тесты прошли | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-STR-2 | Выделенный модуль cryptocore.csprng | `test_signature_and_lengths` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-STR-3 | README и TESTING: автоматический ключ, свойства RNG, процедура STS | `test_generated_key_roundtrip_all_modes`, `test_uses_os_urandom` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-CLI-1 | Отсутствие --key разрешено при шифровании | `test_generated_key_roundtrip_all_modes` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-CLI-2 | Явный ключ используется без изменения | `test_supplied_key_unchanged_and_weak_warning` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-CLI-3 | Новый ключ 16 байт, hex stdout и продолжение шифрования | `test_generated_key_roundtrip_all_modes`, `test_key_printed_immediately_once_and_never_serialized` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-CLI-4 | --key обязателен при расшифровании всех режимов | `test_decryption_requires_key_all_modes` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-RNG-1 | Выделенная функция генерации байтов | `test_signature_and_lengths` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-RNG-2 | generate_random_bytes(num_bytes: int) -> bytes | `test_signature_and_lengths`, `test_invalid_counts` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-RNG-3 | Источником является os.urandom | `test_uses_os_urandom` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-RNG-4 | Некриптографического RNG и fallback нет; обзор csprng.py | `test_uses_os_urandom`, `test_os_failures_and_malformed_results` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-RNG-5 | Единый модуль генерирует ключ и все IV | `test_key_printed_immediately_once_and_never_serialized`, `test_1000_ivs_from_shared_generator` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-RNG-6 | Ошибки OS/неверный результат RNG дают понятное исключение/CLI-отказ | `test_os_failures_and_malformed_results`, `test_rng_failures_preserve_output_and_limit_key_output` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-KEY-1 | Автоматический AES-128 ключ имеет длину 16 байт | `test_generated_key_roundtrip_all_modes` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-KEY-2 | Вывод ключа сразу после генерации, ровно один раз | `test_key_printed_immediately_once_and_never_serialized` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-KEY-3 | Формат только IV||C либо C, поля ключа нет | `test_key_printed_immediately_once_and_never_serialized` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-IV-1 | Все четыре IV-режима используют generate_random_bytes | `test_iv_generation_source_and_prefix`, `test_1000_ivs_from_shared_generator` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-IV-2 | Форматы и обработка IV С2 не изменены | `test_all_mode_cli_roundtrips_and_format` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-TEST-1 | Полный цикл со сгенерированным ключом для всех режимов | `test_generated_key_roundtrip_all_modes` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-TEST-2 | Ровно 1000 ключей по 16 байт, повторов нет | `test_1000_unique_keys` | PASSED | [S3 JSON](verification/sprint3.json) |
| S3-TEST-3 | Реальный NIST STS не выполнен; среда недоступна | Фактическая попытка запуска; unittest SKIPPED | BLOCKED | [Проверка среды](verification/nist_availability.json) |
| S3-TEST-5 | Оба направления совместимости С2 сохранены | `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [S3 JSON](verification/sprint3.json) |

Невыполненное обязательство: только S3-TEST-3 (все его STS-подпункты, кроме подготовки данных/документирования процедуры). Выявленных дефектов реализованных функций нет; внешняя статистическая проверка не завершена.
