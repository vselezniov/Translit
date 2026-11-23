# -*- coding: utf-8 -*-
"""
Транслитератор текста с алфавита Мёмы на кириллицу.

Скрипт идёт по тексту слева направо и применяет первое подошедшее правило из списка.
Если правила нет — переводит букву по таблице ALPHABET, сохраняя регистр.

Описание алфавита: https://mbibl.wordpress.com/vyt-xox/

Использование:
    python translit.py                      # файл по умолчанию из data/
    python translit.py глава.txt            # указанный файл
    python translit.py глава.txt -o out.txt # указать файл результата
"""

import argparse
import re
from pathlib import Path


# 1. ПУТИ ПО УМОЛЧАНИЮ
# Файл без указания папки ищется в data/ рядом со скриптом; результат сохраняется рядом с исходником.
DATA_FOLDER = "data"
DEFAULT_INPUT = "Xэtvac-17.txt"
DEFAULT_OUTPUT = "Матфея-17-Translit.txt"


# 2. ТРАНСЛИТЕРАЦИЯ
def translit_text(mjoma_text: str) -> str:
    """Переводит текст с алфавита Мёмы в кириллицу за один проход."""

    def write_for(match: re.Match) -> str:
        rule_number = int(match.lastgroup.removeprefix('rule_'))
        what_we_see, what_we_write = SPELLING_RULES[rule_number]
        return write_cyrillic(match.group(), what_we_write, what_we_see)

    return RULE_FINDER.sub(write_for, mjoma_text)


# 3. ТАБЛИЦА СООТВЕТСТВИЯ БУКВ
# Формат: (строчная алфавита Мёмы, прописная алфавита Мёмы, кириллица).
# В таблицу включены только буквы, имеющие прямой аналог в кириллице.
# Звуки «ш» и «щ» в Мёме передаются одной буквой «w» (выбор буквы задаётся в SH_AND_SHCH).
ALPHABET = [
    ('x', 'X', 'м'),   ('r', 'Г', 'б'),   ('l', 'L', 'п'),   ('k', 'K', 'н'),
    ('ʌ', 'Ʌ', 'в'),   ('v', 'V', 'ф'),   ('f', 'F', 'д'),   ('t', 'T', 'т'),
    ('z', 'Z', 'з'),   ('s', 'S', 'с'),   ('b', 'Б', 'г'),   ('p', '⸤P⸥', 'к'),
    ('g', 'E', 'х'),   ('h', 'H', 'р'),   ('μ', 'Ч', 'л'),   ('q', '∀', 'ц'),
    ('ɥ', '⸤Ч⸥', 'ч'), ('ʍ', 'M', 'ж'),   ('w', 'W', 'ш'),   ('d', 'D', 'о'),
    ('ɑ', 'O', 'ё'),   ('э', 'Э', 'а'),   ('c', 'C', 'я'),   ('e', 'P', 'э'),
    ('a', 'B', 'е'),   ('n', 'Ո', 'у'),   ('u', 'U', 'ю'),
    ('ⲗ', '⅄', 'ы'),   ('y', 'Y', 'и'),   ('ў', 'Ў', 'й'),   ('i', 'I', 'ъ'),
    ('j', 'J', 'ь'),
]

# Спецзнаки правил замены:
#   _    граница слова (внутри [...] запрещён)
#   {н}  вставка отсутствующей буквы
#   ∅    пропуск буквы оригинала
#   ⁀    удаление пробела при склейке слов

# 1. Слитное написание раздельно написанных слов
JOINED_WORDS = [
    ('_kэ sɥɑt',      'на⁀счёт'),
    ('_kэ spdμjpd',   'на⁀сколько'),
    ('_ka sxdthc',    'не⁀смотря'),
    ('_ka ʌdzxdʍkd',  'не⁀возможно'),
]

# 2. Удвоенные согласные
# 2а. «нн» в основах (цикл добавляет «_» слева и «{н}» справа)
DOUBLE_N_IN_STEMS = [
    (f'_{mjoma}', f'{russian}{{н}}')
    for mjoma, russian in {
        'razʌyk(?=ⲗg)':      'безвин',
        'razfdk':            'бездон',
        'ʌdak':              'воен',
        'bμnryk(?=ⲗ)':       'глубин',
        'fэk(?=dʌ)':         'дан',
        'fhck':              'дрян',
        'ʍeμэk':             'желан',
        'zэμdʍek':           'заложен',
        'zэxэzэk':           'замазан',
        'yxak(?=d)':         'имен',
        'ykvdhxэqⲗdk':       'информацион',
        'ydэk(?=э)':         'иоан',
        'ystyk(?=d)':        'истин',
        'kaysldhɥak':        'неиспорчен',
        'katμak':            'нетлен',
        'drⲗfak':            'обыден',
        'dstэʌμak':          'оставлен',
        'ldfʌahʍek(?=d)':    'подвержен',
        'ldfμyk':            'подлин',
        'ldstdck':           'постоян',
        'lhazhak(?=d)':      'презрен',
        'lhyzʌэk(?=d|ⲗў)':   'призван',
        'lhyhnɥak':          'приручен',
        'lhdpэʍdk(?=d|ⲗў)':  'прокажён',
        'hэʌkdqek':          'равноцен',
        'sʌcwak(?=[ⲗdэ]|yp)': 'священ',
        'sdʌahwek':          'совершен',
        'nrhэk(?=d|ⲗў)':     'убран',
        'nʌahak(?=d)':       'уверен',
        'nʌyfak':            'увиден',
        'nkyɥtdʍek(?=ⲗg)':   'уничтожен',
        'nsμdʌμak(?=d|ⲗў)':  'условлен',
        'nthэɥak':           'утрачен',
    }.items()
]

# 2б. «нн» в суффиксах (в кратких формах остаётся одна «н»)
DOUBLE_N_IN_SUFFIXES = [
    ('wɑk(?!dp)(?=[ⲗэdcau])',  'щён{н}'),
    ('ɑk(?!dp)(?=[ⲗэdcau])',   'ён{н}'),
    ('stʌak(?!_)',             'ствен{н}'),
]

# 2в. Удвоенные согласные в корнях
DOUBLE_IN_ROOTS = [
    ('_эldμds',        'апол{л}ос'),
    ('_raznr(?=э)',    'без{з}уб'),
    ('_pdμdsэμ',       'колос{с}ал'),
    ('_xэs(?=dў|э_)',  'мас{с}'),
    ('_xyμyd',         'мил{л}ио'),
    ('_xysy',          'мис{с}и'),
    ('_drasyμak',      'обес{с}илен'),
    ('_lэsyʌ',         'пас{с}ив'),
    ('_lhdqes',        'процес{с}'),
]

# 3. Словарные исключения
EXCEPTIONS = [
    ('_tⲗscɥcμat',    'тысячелет'),
    ('_xэwtэr(?=k)',  'ма{с}штаб'),
    ('_drjafak',      'объедин'),
    ('_kakэʌyfaxэ_',  'ненавидима'),
    ('_lhdywe',       'прои{с}ше'),
    ('_pdlahkэnx',    'капернаум'),
    ('_kdɥ_',         'ноч{ь}'),
    ('_saʌdfkc',      'сегодня'),
    ('_eμэ_',         'эл{л}а'),
    ('_эgyw_',        'ахиш'),
]

# 4. Окончания
# 4а. Родительный падеж (-ого/-его) и исключения с -ова/-ово в корне
GENITIVE_ENDINGS = [
    ('_yэpdʌэ_',           'иакова'),
    ('_sμdʌd_',            'слово'),
    ('_sμdʌэ_',            'слова'),
    ('_skdʌэ_',            'снова'),
    ('wdʌ[dэ]_',           'шого'),
    ('(?<=[dɑea])ʌ[dэ]_',  'го'),
]

# 4б. Глагольные окончания 2-го лица ед. числа
VERB_ENDINGS = [
    ('(?<=[eayɑ])wsc_',  'ш{ь}ся'),
    ('(?<=[eayɑ])w_',    'ш{ь}'),
]

# 5. Правописание после шипящих и «ц»
# 5а. После «ж»
AFTER_ZH = [
    ('ʍdμ',                   'жёл'),
    ('ʍdk(?=j?[dɑэceanuⲗy])', 'жён'),  # перед гласной — «ё» (жёны), перед согласной — «о» (жонглёр)
    ('ʍdt',                   'жёт'),
    ('ʍe',                    'же'),
    ('ʍⲗ',                    'жи'),
    ('ʍi',                    'жь'),
]

# 5б. Выбор «ш»/«щ» для буквы «w» и о/ё после них
SH_AND_SHCH = [
    ('wɑ',             'щё'),
    ('wc',             'ща'),
    ('wa',             'ще'),
    ('wu',             'щу'),
    ('wy',             'щи'),
    ('wⲗ',             'ши'),
    ('we',             'ше'),
    ('wd_',            'шо'),
    ('wda_',           'шое'),
    ('wdў_',           'шой'),
    ('wdxn_',          'шому'),
    ('wdx_',           'шом'),
    ('wdu_',           'шою'),
    ('wd',             'шё'),
    ('wj(?=[ɑcauy])',  'щь'),
    ('wj_',            'щь'),
    ('wj',             'щ∅'),
]

# 5в. После «ц» и «ч»
AFTER_TS_CH = [
    ('qⲗ(?!_)',  'ци'),
    ('ɥc',       'ча'),
    ('ɥu',       'чу'),
]

# 6. Замена «э» на «е» после т, с, ц
SOFTENED_E = [
    ('qe',  'це'),
    ('te',  'те'),
    ('se',  'се'),
]

# 7. Разделительный «ъ» после приставок
HARD_SIGN = [
    ('_drj(?=[ɑcau])',   'объ'),
    ('_ldfj(?=[ɑcau])',  'подъ'),
    ('_kэfj(?=[ɑcau])',  'надъ'),
    ('_yzj(?=[ɑcau])',   'изъ'),
    ('_hэzj(?=[ɑcau])',  'разъ'),
    ('_sj(?=[ɑcau])',    'съ'),
]

# Порядок определяет приоритет: частные правила идут раньше общих.
SPELLING_RULES = (
    JOINED_WORDS
    + DOUBLE_N_IN_STEMS + DOUBLE_N_IN_SUFFIXES + DOUBLE_IN_ROOTS
    + EXCEPTIONS
    + GENITIVE_ENDINGS + VERB_ENDINGS
    + AFTER_ZH + SH_AND_SHCH + AFTER_TS_CH
    + SOFTENED_E
    + HARD_SIGN
    + [(small, cyrillic) for small, _, cyrillic in ALPHABET]
)

# 5. КОМПИЛЯЦИЯ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ
CAPITAL_OF = {small: capital for small, capital, _ in ALPHABET}
CAPITAL_LETTERS = frozenset(CAPITAL_OF.values())

# Сортировка по убыванию длины: составные знаки (например, «⸤P⸥») проверяются раньше одиночных.
ALL_LETTERS = sorted(
    [letter for small, capital, _ in ALPHABET for letter in (small, capital)],
    key=len,
    reverse=True,
)

MJOMA_LETTER_PATTERN = '|'.join(re.escape(letter) for letter in ALL_LETTERS)
MJOMA_LETTER = re.compile(MJOMA_LETTER_PATTERN)

one_char_letters = ''.join(re.escape(x) for x in ALL_LETTERS if len(x) == 1)
compound_letters = [x for x in ALL_LETTERS if len(x) > 1]

WORD_START = ''.join(f'(?<!{re.escape(x)})' for x in compound_letters) + f'(?<![{one_char_letters}])'
WORD_END = f'(?!{MJOMA_LETTER_PATTERN})'


def any_case(letter: str) -> str:
    """Шаблон для поиска буквы в обоих регистрах."""
    return f'(?:{re.escape(CAPITAL_OF[letter])}|{re.escape(letter)})'


def any_of(letters: str) -> str:
    """Символьный класс для группы букв в обоих регистрах."""
    if '_' in letters:
        raise ValueError(
            f"Символ «_» недопустим внутри [{letters}]. Используйте «(?=[…]|_)»."
        )
    return '[' + ''.join(re.escape(CAPITAL_OF[x]) + re.escape(x) for x in letters) + ']'


def search_pattern(what_we_see: str) -> str:
    """Преобразует шаблон правила в регулярное выражение."""
    pieces = []
    position = 0

    while position < len(what_we_see):
        symbol = what_we_see[position]

        if symbol == '[':
            closing = what_we_see.index(']', position)
            pieces.append(any_of(what_we_see[position + 1:closing]))
            position = closing
        elif symbol == '_':
            at_word_start = position == 0 or what_we_see[position - 1] in '(=<'
            pieces.append(WORD_START if at_word_start else WORD_END)
        elif symbol in CAPITAL_OF:
            pieces.append(any_case(symbol))
        else:
            pieces.append(symbol)
        position += 1

    return ''.join(pieces)


RULE_FINDER = re.compile('|'.join(
    f'(?P<rule_{number}>{search_pattern(what_we_see)})'
    for number, (what_we_see, _) in enumerate(SPELLING_RULES)
))


# 6. СБОРКА РЕЗУЛЬТАТА С УЧЁТОМ РЕГИСТРА
WRITING_SIGNS = re.compile(r'\{(.)\}|(∅)|(⁀)|(.)')


def write_cyrillic(fragment: str, what_we_write: str, what_we_see: str) -> str:
    """Переводит найденный фрагмент в кириллицу, сохраняя регистр."""
    seen_letters = MJOMA_LETTER.findall(fragment)
    signs = WRITING_SIGNS.findall(what_we_write)

    pairs = sum(1 for _, skipped, _, written in signs if skipped or written)
    if pairs != len(seen_letters):
        raise ValueError(
            f"Ошибка длины в правиле {what_we_see!r}: поймано {len(seen_letters)} "
            f"букв ({fragment!r}), в замене указано {pairs}. Проверьте {{}} и ∅."
        )

    cyrillic = []
    letters_to_pair = iter(seen_letters)
    capital = False
    just_glued = False

    for inserted, skipped, glued, written in signs:
        if glued:
            just_glued = True
        elif inserted:
            cyrillic.append(inserted.upper() if capital else inserted)
        else:
            seen = next(letters_to_pair)
            if not just_glued:
                capital = seen in CAPITAL_LETTERS
            just_glued = False
            if written:
                cyrillic.append(written.upper() if capital else written)

    return ''.join(cyrillic)


# 7. ЗАПУСК
def resolve_input_path(name: str) -> Path:
    """Ищет входной файл по указанному пути или в папке DATA_FOLDER."""
    path = Path(name)
    if path.is_absolute() or path.exists():
        return path
    return Path(__file__).resolve().parent / DATA_FOLDER / path


def main() -> None:
    parser = argparse.ArgumentParser(description="Транслитерация Мёма → кириллица")
    parser.add_argument('input', nargs='?', default=DEFAULT_INPUT, help="файл с текстом на Мёме")
    parser.add_argument('-o', '--output', help="файл результата")
    args = parser.parse_args()

    input_path = resolve_input_path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_name(DEFAULT_OUTPUT)

    mjoma_text = input_path.read_text(encoding='utf-8-sig')
    cyrillic_text = translit_text(mjoma_text)
    output_path.write_text(cyrillic_text, encoding='utf-8')

    print(cyrillic_text)
    print(f"\nГотово! Результат сохранён в: {output_path}")


if __name__ == '__main__':
    main()