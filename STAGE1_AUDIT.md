# CryptoCore — финальная приёмка Спринтов 1–3

Дата: 2026-11-09. Windows 11, Python 3.14.0, PyCryptodome 4.3.0.

**Все 57/57 Must — PASSED. S3-TEST-3 закрыт реальным NIST STS 2.1.2. Блокирующих требований С1–С3 нет; этап 1 принят. Спринт 4 не начинался.**

## Текущее состояние и повторная проверка

С1–С3 реализованы ранее; разработка заново не начиналась. AES-128 ECB/CBC/CFB-128/OFB/CTR, PKCS#7, CSPRNG, CLI и атомарный IO не менялись. Учитываются E01/C04/C05: автоматический encrypt-key с С3, ECB без IV, явный --iv означает raw C. Исходное ТЗ сохранено побайтово.

Регрессия после STS и обновления приёмочной проверки: **62 PASSED, 0 FAILED, 0 ERROR, 0 SKIPPED**, 86.109 с. [JSON](verification/nist_sts_regression.json), [лог](verification/nist_sts_regression.log). До этого целевой `NISTSTSAvailabilityTests` прошёл отдельно. Старые sprint*.json/stage1_final и результаты 6 ноября — исторические контрольные точки, не доказательства нового запуска.

| Спринт | Must | PASSED | FAILED | BLOCKED | NOT_VERIFIED |
| :-- | --: | --: | --: | --: | --: |
| 1 | 16 | 16 | 0 | 0 | 0 |
| 2 | 19 | 19 | 0 | 0 | 0 |
| 3 | 22 | 22 | 0 | 0 | 0 |
| Всего | 57 | 57 | 0 | 0 | 0 |

## Все 57 Must

ID/приоритеты/подпункты сверены с оригинальными m1–m3. Полные ID тестов, исходные строки и доказательства: [реестр](verification/stage1_requirements_recheck.json). В таблицах указаны методы нового прогона; для структуры/документов также сохранён [обзор](verification/stage1_review.json). Упаковка и отдельный установленный wheel были проверены 6 ноября: [packaging](verification/stage1_packaging_recheck.json), [wheel-тесты](verification/stage1_wheel_tests.json). В текущем задании работающие криптомодули/CLI не менялись.

### Спринт 1

| ID | Реализовано | Как проверено | Статус | Доказательство |
| :-- | :-- | :-- | :-- | :-- |
| S1-STR-1 | Локальный Git и правила исключения | `test_git_packaging_and_readme` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-STR-2 | README: назначение, установка/сборка, зависимости, CLI и полный цикл | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-STR-3 | pyproject.toml; новая сборка и установка wheel | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CLI-1 | Установленный cryptocore.exe запускается | `test_entrypoint_and_roundtrip` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CLI-2 | Полный набор аргументов AES-128 ECB и одна операция | `test_entrypoint_and_roundtrip`, `test_missing_and_conflicting_arguments` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CLI-3 | Строгий hex-ключ ровно 16 байт | `test_invalid_values_and_future_features` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CLI-4 | Валидация аргументов, stderr и ненулевые коды | `test_invalid_values_and_future_features`, `test_missing_and_conflicting_arguments` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CRY-1 | Только AES-128, блок и ключ 16 байт | `test_fips197_known_answer`, `test_reject_invalid_keys` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CRY-2 | Crypto.Cipher.AES как одноблочный примитив; собственных раундов нет | `test_fips197_known_answer`, `test_sp800_38a_all_ecb_blocks`, `test_only_single_block_library_aes_and_os_rng` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CRY-3 | Собственный ECB поверх вызовов одного блока | `test_nist_file_prefix_and_decryption`, `test_all_lengths_and_chunk_boundaries` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CRY-4 | Собственный PKCS#7: полное дополнение и строгая проверка | `test_every_padding_length`, `test_invalid_padding`, `test_padding_failure_preserves_or_does_not_create_output` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-CRY-5 | Бинарные потоки, текст UTF-8 и произвольные байты | `test_entrypoint_and_roundtrip` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-IO-1 | Чтение всего входа чанками, память ограничена | `test_file_chunk_independence`, `test_bounded_memory` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-IO-2 | Запись результата и атомарная публикация | `test_entrypoint_and_roundtrip`, `test_replace_and_sync_failures_preserve_output` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-IO-3 | Ошибки файлов: stderr, код 1, сохранность результата | `test_file_errors_preserve_existing_output`, `test_read_and_write_failures`, `test_midstream_failure_preserves_output` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S1-TEST-1 | Полный цикл побайтово для пустых/бинарных/граничных файлов | `test_entrypoint_and_roundtrip`, `test_all_lengths_and_chunk_boundaries` | PASSED | [регрессия](verification/nist_sts_regression.json) |

### Спринт 2

| ID | Реализовано | Как проверено | Статус | Доказательство |
| :-- | :-- | :-- | :-- | :-- |
| S2-STR-1 | Структура, упаковка и регрессия С1 сохранены | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-STR-2 | README описывает новые режимы, IV и исполняемые сценарии OpenSSL | `test_all_mode_cli_roundtrips_and_format`, `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-STR-3 | Четыре режима в src/cryptocore/modes | `test_cbc_nist`, `test_cfb128_nist`, `test_ofb_nist`, `test_ctr_nist` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-CLI-1 | CLI принимает cbc/cfb/ofb/ctr | `test_all_mode_cli_roundtrips_and_format` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-CLI-2 | Случайный IV для encrypt; hex-IV только для decrypt | `test_iv_argument_rules`, `test_iv_generation_source_and_prefix` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-CRY-1 | AES-128 и библиотечный блок сохранены | `test_fips197_known_answer`, `test_reject_invalid_keys` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-CRY-2 | Все четыре режима реализованы самостоятельно | `test_cbc_nist`, `test_cfb128_nist`, `test_ofb_nist`, `test_ctr_nist`, `test_independent_oracle_and_chunks`, `test_only_single_block_library_aes_and_os_rng` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-CRY-3 | CBC chaining, CFB-128, OFB feedback, big-endian CTR | `test_cbc_nist`, `test_cfb128_nist`, `test_ofb_nist`, `test_ctr_nist`, `test_counter_carry_and_exhaustion` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-CRY-4 | PKCS#7 только ECB/CBC; потоковые режимы сохраняют длину | `test_independent_oracle_and_chunks`, `test_all_mode_cli_roundtrips_and_format` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-IV-1 | os.urandom(16), отказ при ошибке RNG | `test_iv_generation_source_and_prefix`, `test_rng_failure_preserves_output`, `test_uses_os_urandom` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-IV-2 | IV16 записывается префиксом перед C | `test_iv_generation_source_and_prefix`, `test_all_mode_cli_roundtrips_and_format` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-IV-3 | Чтение IV-префикса либо весь вход как raw C при --iv | `test_all_mode_cli_roundtrips_and_format` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-IV-4 | Ровно 16 байт для четырёх IV-режимов; ECB без IV | `test_invalid_iv_and_mode`, `test_iv_argument_rules` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-IO-1 | Префикс записывается раньше шифртекста | `test_iv_generation_source_and_prefix`, `test_file_chunks_all_modes` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-IO-2 | Без --iv первые 16 байт снимаются с того же input handle | `test_all_mode_cli_roundtrips_and_format`, `test_file_chunks_all_modes` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-IO-3 | Усечённый IV отклоняется без порчи output | `test_short_iv_and_cbc_corruption_preserve_output` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-TEST-1 | Полный цикл для всех новых режимов | `test_all_mode_cli_roundtrips_and_format` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-TEST-2 | CryptoCore -> OpenSSL для всех четырёх режимов | `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S2-TEST-3 | OpenSSL -> CryptoCore для всех четырёх режимов | `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [регрессия](verification/nist_sts_regression.json) |

### Спринт 3

| ID | Реализовано | Как проверено | Статус | Доказательство |
| :-- | :-- | :-- | :-- | :-- |
| S3-STR-1 | Упаковка/структура С1-С2 сохранены; прежние тесты прошли | `test_git_packaging_and_readme`, `test_entrypoint_and_roundtrip` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-STR-2 | Выделенный модуль cryptocore.csprng | `test_signature_and_lengths` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-STR-3 | README и TESTING: автоматический ключ, свойства RNG, процедура STS | `test_generated_key_roundtrip_all_modes`, `test_uses_os_urandom` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-CLI-1 | Отсутствие --key разрешено при шифровании | `test_generated_key_roundtrip_all_modes` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-CLI-2 | Явный ключ используется без изменения | `test_supplied_key_unchanged_and_weak_warning` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-CLI-3 | Новый ключ 16 байт, hex stdout и продолжение шифрования | `test_generated_key_roundtrip_all_modes`, `test_key_printed_immediately_once_and_never_serialized` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-CLI-4 | --key обязателен при расшифровании всех режимов | `test_decryption_requires_key_all_modes` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-RNG-1 | Выделенная функция генерации байтов | `test_signature_and_lengths` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-RNG-2 | generate_random_bytes(num_bytes: int) -> bytes | `test_signature_and_lengths`, `test_invalid_counts` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-RNG-3 | Источником является os.urandom | `test_uses_os_urandom` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-RNG-4 | Некриптографического RNG и fallback нет; обзор csprng.py | `test_uses_os_urandom`, `test_os_failures_and_malformed_results`, `test_only_single_block_library_aes_and_os_rng` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-RNG-5 | Единый модуль генерирует ключ и все IV | `test_key_printed_immediately_once_and_never_serialized`, `test_1000_ivs_from_shared_generator` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-RNG-6 | Ошибки OS/неверный результат RNG дают понятное исключение/CLI-отказ | `test_os_failures_and_malformed_results`, `test_rng_failures_preserve_output_and_limit_key_output` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-KEY-1 | Автоматический AES-128 ключ имеет длину 16 байт | `test_generated_key_roundtrip_all_modes` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-KEY-2 | Вывод ключа сразу после генерации, ровно один раз | `test_key_printed_immediately_once_and_never_serialized` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-KEY-3 | Формат только IV\|\|C либо C, поля ключа нет | `test_key_printed_immediately_once_and_never_serialized` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-IV-1 | Все четыре IV-режима используют generate_random_bytes | `test_iv_generation_source_and_prefix`, `test_1000_ivs_from_shared_generator` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-IV-2 | Форматы и обработка IV С2 не изменены | `test_all_mode_cli_roundtrips_and_format` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-TEST-1 | Полный цикл со сгенерированным ключом для всех режимов | `test_generated_key_roundtrip_all_modes` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-TEST-2 | Ровно 1000 ключей по 16 байт, повторов нет | `test_1000_unique_keys` | PASSED | [регрессия](verification/nist_sts_regression.json) |
| S3-TEST-3 | Официальный NIST STS 2.1.2: 15/15 семейств и 188/188 подтестов; 800 потоков, корректный учёт применимости. | `test_official_nist_sts_all_15` | PASSED | [регрессия](verification/nist_sts_regression.json), [NIST STS](NIST_STS_REPORT.md), [сырые отчёты](verification/nist_sts_raw_reports.zip) |
| S3-TEST-5 | Оба направления совместимости С2 сохранены | `test_cbc_both_directions`, `test_cfb128_both_directions`, `test_ofb_both_directions`, `test_ctr_both_directions` | PASSED | [регрессия](verification/nist_sts_regression.json) |

## OpenSSL и AES KAT

Новый прогон реально выполнил OpenSSL 3.5.3 в обоих направлениях для всех пяти режимов; пропусков нет. Проверены FIPS 197 AES-128 и полный предоставленный набор четырёхблочных SP 800-38A векторов для ECB/CBC/CFB-128/OFB/CTR. Это KAT проекта, не сертификация CAVP. PKCS#7 проверен на всех размерах дополнения, пустом/кратном входе и неправильных длинах/байтах; потоковые режимы не дополняются. Проверены граничные длины, чанки, перенос/исчерпание CTR.

## CSPRNG и NIST STS

Общий os.urandom-провайдер проверен на длинах, неправильных параметрах и отказах. Ключ выводится ровно один раз, не включается в C; явный ключ сохраняется; IV генерируются тем же модулем. Полный цикл выполнен во всех режимах. В новой регрессии уникальных ключей: 1000/1000; IV: 1000/1000; доля единичных битов 0.50109375. Эти smoke-проверки не подменяют STS.

Официальный STS 2.1.2 проверил фиксированные 100 000 000 байт (800 × 1 000 000 бит) за 306.343 с. **15/15 семейств и 188/188 подтестов прошли второй уровень.** У Excursions/Variant 496 применимых потоков; 304 неприменимых не засчитаны успешными. Все p-values, пропорции, параметры, исходные журналы, калибровка и ограничения — в [NIST_STS_REPORT.md](NIST_STS_REPORT.md) и [результатах](verification/nist_sts_results.json).

## Ошибки, сохранность файлов и исправления

Регрессия проверила отсутствующие/неверные пути, Windows-блокировки через CreateFileW, кириллицу/пробелы, одинаковые файлы/hard links, усечённые IV/блоки, ошибки аргументов, padding, RNG, частичной записи/чтения, fsync/replace и удаление временных файлов. Прежний output сохраняется при ошибках. Произвольная подмена неаутентифицируемого C не обязана обнаруживаться; AEAD не добавлялась.

Дефектов криптографических модулей не обнаружено, они не исправлялись. Снят только внешний блокер STS: согласованный локальный Zig, оригинальная сборка без патчей, реальный прогон, замена безусловного skip на проверку артефактов. Вспомогательная проверка wheel учитывает новый результат без прежнего ожидания обязательного skip. Системные компоненты/настройки не менялись. Исторические отчёты сохранены; прежние версии текущих документов находятся в artifacts/nist_sts_20261109/history/.

Все семь Should С1–С3 также подтверждены; Could S1-CLI-5 (автоимя output) не реализован. Локальный Git унаследован без commits/remotes, index/история не менялись. Это не дополнительный Must; исходный STR-1 требует Git-репозиторий, а не конкретный remote/commit.

## Установка и запуск

```powershell
.\.venv\Scripts\python.exe -m pip install --no-build-isolation -e .
.\.venv\Scripts\cryptocore.exe --help
.\.venv\Scripts\python.exe tests/run_tests.py --report verification/local.json
```

После установки CLI:

```powershell
.\.venv\Scripts\cryptocore.exe --algorithm aes --mode cbc --encrypt --key 2b7e151628aed2a6abf7158809cf4f3c --input plain.bin --output cipher.bin
.\.venv\Scripts\cryptocore.exe --algorithm aes --mode cbc --decrypt --key 2b7e151628aed2a6abf7158809cf4f3c --input cipher.bin --output restored.bin
```

plain.bin — подготовленный тестовый файл; сравнивать bytes через Python. Для автоматического ключа убрать --key только при encrypt, сохранить выведенный ключ и передать decrypt. Подробная установка/сборка — [README](README.md), запуск STS и сохранение его артефактов — [TESTING](TESTING.md).

## Вердикт

**Спринты 1–3 приняты: 57/57 Must PASSED, незакрытых блокирующих требований этапа нет. Готовность по обязательствам этапа 1 к следующему спринту подтверждена. Спринт 4 не начинался; работа остановлена после приёмки.**
