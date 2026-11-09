# CryptoCore

Учебная потоковая CLI-утилита шифрования файлов AES-128; собственные режимы поверх библиотечного AES-блока.

## Установка и сборка (PowerShell, Python 3.14)

Из корня проекта, используя существующее виртуальное окружение:

```powershell
.\.venv\Scripts\python.exe -m pip install setuptools==82.0.1 wheel==0.46.3 packaging==26.3
.\.venv\Scripts\python.exe -m pip install --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pip wheel --no-build-isolation --no-deps . --wheel-dir dist
.\.venv\Scripts\Activate.ps1
cryptocore --help
```

Без активации используйте `.\.venv\Scripts\cryptocore.exe`. Runtime: Python 3.14 и `pycryptodome==4.3.0`. Сборка: setuptools 82.0.1, wheel 0.46.3, packaging 26.3. Тесты: стандартный unittest; внешний OpenSSL нужен только для совместимости. Глобальная настройка Windows не требуется.

## Спринт 1: ECB

Ровно один из `--encrypt`/`--decrypt`. Ключ — 32 hex-символа (16 байт); поддерживается только AES-128. В С1/С2 ключ был обязательным для обеих операций; с С3 при шифровании он может генерироваться (см. ниже). `--algorithm`, `--mode`, `--input`, `--output` обязательны. Вход/выход бинарные, пути с пробелами заключайте в кавычки.

```powershell
cryptocore --algorithm aes --mode ecb --encrypt --key 000102030405060708090a0b0c0d0e0f --input plain.bin --output cipher.bin
cryptocore --algorithm aes --mode ecb --decrypt --key 000102030405060708090a0b0c0d0e0f --input cipher.bin --output restored.bin
.\.venv\Scripts\python.exe -c "from pathlib import Path; assert Path('plain.bin').read_bytes() == Path('restored.bin').read_bytes()"
```

Для воспроизводимого примера сначала создайте `plain.bin`:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; Path('plain.bin').write_bytes(bytes(range(256)))"
```

ECB-файл содержит только шифртекст с PKCS#7: полный блок padding добавляется и к пустому/кратному входу. Собственная логика разбивает поток на блоки, каждый вызов PyCryptodome обрабатывает только 16 байт. AES-раунды не реализуются заново. ECB предназначен для учебного изучения; режим не обеспечивает аутентификацию.

При неверном формате/аргументах код 2, при ошибке IO/padding — 1, при успехе — 0. Диагностика идёт в stderr. Выход публикуется через временный файл только после успеха; прежний output сохраняется при сбое. Одинаковые вход/выход и файловые алиасы отклоняются.

## Спринт 2: CBC, CFB-128, OFB, CTR

`--mode` принимает `cbc`, `cfb`, `ofb`, `ctr` и прежний `ecb`. CBC использует PKCS#7; CFB (сегмент 128 бит), OFB и CTR не дополняют данные, длина C равна длине входа. CTR увеличивает весь 128-битный big-endian счётчик из IV, отказывает при его исчерпании. Все режимы написаны в проекте, готовые библиотечные режимы служат только эталонами в тестах.

При шифровании IV генерируется через единый CSPRNG (`os.urandom(16)`), записывается перед C; пользовательский `--iv` запрещён. При расшифровании без `--iv` из файла снимаются первые 16 байт. При явном hex `--iv` **весь вход** считается сырым C без префикса. Угадывания формата нет. ECB IV не принимает и сохраняет прежний формат.

```powershell
cryptocore --algorithm aes --mode cbc --encrypt --key 2b7e151628aed2a6abf7158809cf4f3c --input plain.bin --output cbc.bin
cryptocore --algorithm aes --mode cbc --decrypt --key 2b7e151628aed2a6abf7158809cf4f3c --input cbc.bin --output restored.bin
```

Те же вызовы с `--mode cfb`, `--mode ofb`, `--mode ctr` используют соответствующий режим. Неверная длина IV, усечённый заголовок и неверный CBC padding — ошибки; повреждение потокового C не обнаруживается без аутентификации (она появится в следующих этапах).

### Воспроизводимая совместимость с OpenSSL для всех четырёх режимов

```powershell
.\.venv\Scripts\python.exe -m unittest tests.integration.test_s2_io_openssl.ModesOpenSSLTests -v
```

Этот сценарий реально выполняет оба направления для CBC, CFB-128, OFB, CTR на длинах 0/1/15/16/17/256, проверяет точные байты C и восстановленного файла. Для ручной проверки CBC:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; d=Path('cbc.bin').read_bytes(); Path('iv.hex').write_text(d[:16].hex()); Path('raw.bin').write_bytes(d[16:])"
$ivHex = Get-Content -Raw iv.hex
openssl enc -aes-128-cbc -d -nosalt -K 2b7e151628aed2a6abf7158809cf4f3c -iv $ivHex -in raw.bin -out openssl-restored.bin
openssl enc -aes-128-cbc -nosalt -K 2b7e151628aed2a6abf7158809cf4f3c -iv $ivHex -in plain.bin -out openssl-cipher.bin
cryptocore --algorithm aes --mode cbc --decrypt --key 2b7e151628aed2a6abf7158809cf4f3c --iv $ivHex --input openssl-cipher.bin --output restored.bin
```

Для остальных режимов заменить `cbc` соответственно на `cfb`, `ofb`, `ctr`. OpenSSL `-aes-128-cfb` означает CFB-128, не CFB8; CTR использует полный IV/счётчик. Проверку равенства файлов выполнять Python-командой из примера С1. OpenSSL не получает IV-префикс как часть C и не использует парольный заголовок `Salted__`.

## Тестирование

### Спринт 3: ключи и случайность

`cryptocore.csprng.generate_random_bytes(num_bytes: int) -> bytes` использует только `os.urandom()`, без некриптографического fallback. Все IV и автоматические AES-ключи получаются через эту функцию. Ошибка источника случайности останавливает операцию с понятным stderr; старый output сохраняется. ОС предоставляет криптографический источник; smoke-тесты распределения не доказывают стойкость генератора.

Без `--key` при шифровании генерируется 16-байтный ключ. Сразу после генерации stdout содержит **ровно одну** строку `[INFO] Generated random key: HEX`, затем продолжается шифрование. Пользователь обязан сохранить этот ключ самостоятельно: в файл с C он не включается. Для расшифрования `--key` всегда обязателен. При явном ключе поведение прежнее; повторяющиеся/последовательные байты вызывают предупреждение в stderr без изменения ключа.

```powershell
cryptocore --algorithm aes --mode ctr --encrypt --input plain.bin --output generated.bin
# Скопируйте 32 hex-символа из строки Generated random key вместо KEY_HEX ниже.
cryptocore --algorithm aes --mode ctr --decrypt --key KEY_HEX --input generated.bin --output restored.bin
```

`KEY_HEX` — обозначение фактически напечатанного ключа, не буквальный аргумент. В этом учебном этапе ключ печатается по явному Must; не сохраняйте его в общий журнал или систему контроля версий. Спринты 4–8 ещё не реализованы.

### Общий запуск

```powershell
.\.venv\Scripts\python.exe tests/run_tests.py
```

Проверки включают официальные NIST AES/ECB-векторы, padding, граничные длины, бинарные данные, CLI, атомарность и память. OpenSSL определяется через PATH, переменную `OPENSSL_EXE` или стандартное расположение Git for Windows. Наличие инструмента проверяется фактическим вызовом; при отсутствии внешний тест отмечается как пропущенный.

Теперь набор также проверяет все пять режимов, единый CSPRNG, 1000 ключей и 1000 IV без повторов, вес Хэмминга и инъекции сбоев. Runner возвращает 0 при полном успехе, 1 при провале тестов, **2 при пропуске обязательной внешней проверки**. Официальный NIST STS 2.1.2 выполнен 2026-11-09: все 15 семейств и 188 подтестов прошли на фиксированных 100 МБ. Последняя регрессия: 62 PASSED, без ошибок/пропусков, код 0; 57/57 Must С1–С3 закрыты. Приёмочный тест сверяет сырые отчёты и их происхождение, а не подменяет STS smoke-проверкой. [NIST_STS_REPORT.md](NIST_STS_REPORT.md), [TESTING.md](TESTING.md). Ниже команда генерации старой отдельной выборки; она не воспроизводит принятый эксперимент, для него используйте сохранённые данные и процедуру отчёта:

```powershell
.\.venv\Scripts\python.exe tools/prepare_nist_data.py
.\.venv\Scripts\python.exe tests/run_tests.py --report verification/local.json
```

Сравнение ECB с OpenSSL (совпадающий PKCS#7, без `-nopad`):

Для ручных примеров `openssl` должен быть доступен в текущей оболочке. Если он установлен вместе с Git for Windows, можно задать только локальный alias PowerShell: `Set-Alias -Name openssl -Value 'C:\Program Files\Git\usr\bin\openssl.exe'`. Тестовый runner находит этот путь самостоятельно.

```powershell
openssl enc -aes-128-ecb -nosalt -K 000102030405060708090a0b0c0d0e0f -in plain.bin -out openssl.bin
.\.venv\Scripts\python.exe -c "from pathlib import Path; assert Path('cipher.bin').read_bytes() == Path('openssl.bin').read_bytes()"
```

Официальные источники векторов: [NIST SP 800-38A, приложение F](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38a.pdf), [FIPS 197](https://doi.org/10.6028/NIST.FIPS.197-upd1). Только Python-вариант требований применим к этому проекту.
