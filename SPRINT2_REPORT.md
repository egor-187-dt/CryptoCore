# Спринт 2 — отчёт

Реализован после успешной приёмки С1; отчёт создан **до начала С3**. Все 19 Must — PASSED. С учётом С1 подтверждены 35 Must. Should CLI-3/TEST-4 реализованы; Could не добавлялись.

Команда: `.\.venv\Scripts\python.exe tests/run_tests.py --report verification/sprint2.json`.

Фактический результат: **44 PASSED, 0 FAILED, 0 ERROR, 0 SKIPPED**, 109.345 с, включая все 25 проверок С1. [Лог](verification/sprint2.log), [результаты с версиями и SHA-256](verification/sprint2.json), [ID требований и полные ID тестов](verification/sprint2_requirements.json).

Режимы CBC, CFB-128, OFB, CTR написаны поверх AES128, без библиотечных готовых режимов в рабочем коде. Известные ответы SP 800-38A проверены для каждого режима и обоих направлений; полные четыре блока. Дополнительно независимый PyCryptodome-эталон проверяет разные длины и разбиения чанков. CBC/ECB используют PKCS#7, потоковые режимы не дополняют вход. CTR проверен на переносе и запрете переполнения 128-битного счётчика.

**OpenSSL 3.5.3: оба направления прошли для CBC/CFB-128/OFB/CTR**, длины 0/1/15/16/17/256. Префикс отделяется, `-aes-128-cfb` соответствует CFB-128, CTR использует полный big-endian IV, `-nosalt` исключает парольный контейнер. Сравниваются байты C и восстановленного P. Доступность инструмента подтверждена реальным запуском, пропусков нет.

Проверены IV16, генерация через os.urandom, запрещённый IV при шифровании, обязательная длина, внешний IV/raw C, усечённые заголовки/блоки CBC, ошибки RNG, атомарность, кириллица/пробелы и ограниченная память для новых режимов в обоих направлениях. Регрессия ECB сохранила формат без IV.

Решения C03/C04/C05/C07 реализованы по текущему заданию; C05 для будущего GCM не решается этим этапом. `.gitattributes` сохраняет исходники требований без нормализации байтов. Python/библиотеки прежние: 3.14.0 / PyCryptodome 4.3.0.

## Все Must

| ID | Реализованное поведение | Фактические тесты (полные ID в JSON) | Статус | Доказательство |
| :-- | :-- | :-- | :-- | :-- |
| S2-STR-1 | Структура, упаковка и регрессия С1 сохранены | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-STR-2 | README описывает новые режимы, IV и исполняемые сценарии OpenSSL | `test_all_mode_cli_roundtrips_and_format`, `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-STR-3 | Четыре режима в src/cryptocore/modes | `test_cbc_nist`, `test_cfb128_nist`, `test_ofb_nist`, `test_ctr_nist` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-CLI-1 | CLI принимает cbc/cfb/ofb/ctr | `test_all_mode_cli_roundtrips_and_format` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-CLI-2 | Случайный IV для encrypt; hex-IV только для decrypt | `test_iv_argument_rules`, `test_iv_generation_source_and_prefix` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-CRY-1 | AES-128 и библиотечный блок сохранены | `test_fips197_known_answer`, `test_reject_invalid_keys` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-CRY-2 | Все четыре режима реализованы самостоятельно | `test_cbc_nist`, `test_cfb128_nist`, `test_ofb_nist`, `test_ctr_nist`, `test_independent_oracle_and_chunks` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-CRY-3 | CBC chaining, CFB-128, OFB feedback, big-endian CTR | `test_cbc_nist`, `test_cfb128_nist`, `test_ofb_nist`, `test_ctr_nist`, `test_counter_carry_and_exhaustion` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-CRY-4 | PKCS#7 только ECB/CBC; потоковые режимы сохраняют длину | `test_independent_oracle_and_chunks`, `test_all_mode_cli_roundtrips_and_format` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-IV-1 | os.urandom(16), отказ при ошибке RNG | `test_iv_generation_source_and_prefix`, `test_rng_failure_preserves_output` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-IV-2 | IV16 записывается префиксом перед C | `test_iv_generation_source_and_prefix`, `test_all_mode_cli_roundtrips_and_format` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-IV-3 | Чтение IV-префикса либо весь вход как raw C при --iv | `test_all_mode_cli_roundtrips_and_format` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-IV-4 | Ровно 16 байт для четырёх IV-режимов; ECB без IV | `test_invalid_iv_and_mode`, `test_iv_argument_rules` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-IO-1 | Префикс записывается раньше шифртекста | `test_iv_generation_source_and_prefix`, `test_file_chunks_all_modes` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-IO-2 | Без --iv первые 16 байт снимаются с того же input handle | `test_all_mode_cli_roundtrips_and_format`, `test_file_chunks_all_modes` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-IO-3 | Усечённый IV отклоняется без порчи output | `test_short_iv_and_cbc_corruption_preserve_output` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-TEST-1 | Полный цикл для всех новых режимов | `test_all_mode_cli_roundtrips_and_format` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-TEST-2 | CryptoCore -> OpenSSL для всех четырёх режимов | `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [S2 JSON](verification/sprint2.json) |
| S2-TEST-3 | OpenSSL -> CryptoCore для всех четырёх режимов | `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [S2 JSON](verification/sprint2.json) |

Невыполненных Must С2 и выявленных дефектов нет. С3 можно начинать. Эти режимы не аутентифицируют шифртекст: произвольную подмену потокового C или неверный ключ гарантированно обнаружить нельзя.
