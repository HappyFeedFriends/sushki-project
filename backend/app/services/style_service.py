"""
backend/app/services/style_service.py

Сервис для применения стилей к ответам ИИ.
Готов к использованию на сервере — предоставляет глобальный экземпляр `style_service`.
"""
from typing import Dict
import re
import random


class StyleService:
    """
    Сервис для применения стилей к ответам ИИ
    """

    def __init__(self) -> None:
        self.styles = {
            "business": self._apply_business_style,
            "youth": self._apply_youth_style,
            "direct": self._apply_direct_style,
            "simple": self._apply_simple_style,
        }

        # Словари для замены слов в молодёжном стиле
        self.youth_replacements: Dict[str, str] = {
            # Эмоции и оценка
            "отлично": "имба",
            "хорошо": "топ",
            "плохо": "кринж",
            "смешно": "рофл",
            "понимаю": "жиза",
            "классно": "вайб",
            "стильно": "свэг",
            "круто": "краш",
            # Люди
            "друг": "бро",
            "человек": "чел",
            "обычный человек": "нпс",
            "лидер": "сигма",
            # Действия
            "пропустить": "скипнуть",
            "продвигать": "форсить",
            "раздувать": "хайпить",
            "уйти": "афк",
            "унизить": "слей",
            "хвастаться": "флексить",
        }

        # Эмодзи для разных типов ответов
        self.youth_emojis = {
            "positive": ["😊", "😎", "🔥", "💯", "👌", "✨"],
            "neutral": ["🤔", "👀", "📝", "🔍"],
            "negative": ["😬", "🙈", "⚠️", "💔"],
            "funny": ["😂", "🤣", "😜", "🎉"],
        }

    def apply_style(self, text: str, style_name: str) -> str:
        """
        Применить выбранный стиль к тексту ответа.

        Args:
            text: исходный текст ответа
            style_name: business | youth | direct | simple

        Returns:
            Текст в выбранном стиле
        """
        if not isinstance(text, str):
            text = str(text)
        if style_name not in self.styles:
            # По умолчанию деловой стиль
            style_name = "business"
        style_func = self.styles[style_name]
        try:
            return style_func(text).strip()
        except Exception:
            # На случай ошибки стайлера — вернуть исходный текст
            return text.strip()

    # ------------------ Стили ------------------
    def _apply_business_style(self, text: str) -> str:
        """
        Деловой стиль: строгий, структурированный, официальный
        """
        text = self._remove_emojis(text)

        replacements = {
            "ты": "Вы",
            "тебя": "Вас",
            "тебе": "Вам",
            "твой": "Ваш",
            "твои": "Ваши",
            "твоих": "Ваших",
            "твоим": "Вашим",
        }

        for informal, formal in replacements.items():
            text = re.sub(rf'\b{informal}\b', formal, text, flags=re.IGNORECASE)

        informal_phrases = [
            "короче", "типа", "как бы", "в общем",
            "на самом деле", "честно говоря", "так сказать"
        ]
        for phrase in informal_phrases:
            text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)

        # Структурируем ответ: первый абзац как ввод, остальные маркеры
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        if len(lines) > 1:
            structured = [lines[0]]
            for ln in lines[1:]:
                structured.append(f"• {ln}")
            text = "\n".join(structured)

        if not text.startswith(("Уважаемый", "Здравствуйте")):
            text = f"Уважаемый клиент! {text}"

        return text

    def _apply_youth_style(self, text: str) -> str:
        """
        Молодёжный стиль: сленг, эмодзи, неформальный
        """
        # Удаляем формальные обращения
        text = re.sub(r'Уважаемый клиент!|Здравствуйте!|Уважаемый|Здравствуйте', '', text, flags=re.IGNORECASE).strip()

        # Заменяем слова на сленг
        for formal, slang in self.youth_replacements.items():
            text = re.sub(rf'\b{re.escape(formal)}\b', slang, text, flags=re.IGNORECASE)

        lowered = text.lower()
        emoji = ""
        if any(word in lowered for word in ["отлич", "хорош", "успеш", "правильн"]):
            emoji = self._get_random_emoji("positive")
        elif any(word in lowered for word in ["проблем", "ошибк", "нельзя", "не удалось"]):
            emoji = self._get_random_emoji("negative")
        elif any(word in lowered for word in ["смеш", "шутк", "забав"]):
            emoji = self._get_random_emoji("funny")
        else:
            emoji = self._get_random_emoji("neutral")

        # Добавляем вводную фразу
        youth_intros = ["Короче, ", "Слушай, ", "Бро, ", "Чел, ", "В общем, "]
        if not any(text.startswith(intro) for intro in youth_intros):
            intro = random.choice(youth_intros)
            if text:
                text = intro + text[0].lower() + text[1:]
            else:
                text = intro

        # Префикс эмодзи
        text = f"{emoji} {text}".strip()

        # Иногда добавляем хештеги
        if random.random() > 0.7:
            hashtags = ["#жиза", "#вайб", "#топчик", "#имба", "#челпомоги"]
            selected = random.sample(hashtags, k=random.randint(1, min(2, len(hashtags))))
            text = f"{text} {' '.join(selected)}"

        return text

    def _apply_direct_style(self, text: str) -> str:
        """
        Прямолинейный стиль: кратко, по делу, без воды
        """
        filler_words = [
            "возможно", "вероятно", "наверное", "скорее всего",
            "в общем", "в целом", "так сказать", "честно говоря",
            "должен сказать", "стоит отметить", "следует отметить",
            "хотелось бы отметить", "необходимо подчеркнуть"
        ]
        for word in filler_words:
            text = re.sub(rf'\b{re.escape(word)}[,\s]*', '', text, flags=re.IGNORECASE)

        replacements = {
            "в связи с тем, что": "т.к.",
            "несмотря на то, что": "хотя",
            "для того чтобы": "чтобы",
            "в том случае, если": "если",
            "по причине того, что": "из-за"
        }
        for long, short in replacements.items():
            text = re.sub(re.escape(long), short, text, flags=re.IGNORECASE)

        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        important = []
        for sent in sentences:
            if len(sent.split()) >= 2:
                important.append(sent)
        if len(important) > 3:
            important = important[:3]
        text = '. '.join(important)
        if text and not text.endswith('.'):
            text += '.'
        return text

    def _apply_simple_style(self, text: str) -> str:
        """
        Простой стиль: короткие предложения, простые слова, добрый тон
        """
        simple_replacements = {
            "осуществлять": "делать",
            "предоставлять": "давать",
            "использовать": "применять",
            "необходимо": "нужно",
            "требуется": "надо",
            "осуществляется": "делается",
            "предоставляется": "даётся",
            "означает": "значит"
        }
        for complex_word, simple_word in simple_replacements.items():
            text = re.sub(rf'\b{re.escape(complex_word)}\b', simple_word, text, flags=re.IGNORECASE)

        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        simple_sentences = []
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 10:
                middle = len(words) // 2
                part1 = ' '.join(words[:middle])
                part2 = ' '.join(words[middle:])
                simple_sentences.append(part1 + '.')
                simple_sentences.append(part2.capitalize() + '.')
            else:
                simple_sentences.append(sentence + '.')
        text = ' '.join(simple_sentences)

        kind_intros = ["Привет! ", "Здравствуйте! ", "Добрый день! ", "Приветствую! "]
        if not any(text.startswith(i) for i in kind_intros):
            intro = random.choice(kind_intros)
            text = f"{intro}{text}"

        soft_emojis = ["🙂", "😊", "👍", "👋", "💖", "🌟"]
        if random.random() > 0.5:
            emoji = random.choice(soft_emojis)
            text = f"{text} {emoji}"

        return text

    # ------------------ Утилиты ------------------
    def _remove_emojis(self, text: str) -> str:
        """Удалить эмодзи из текста"""
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def _get_random_emoji(self, category: str) -> str:
        """Получить случайный эмодзи из категории"""
        if category in self.youth_emojis:
            return random.choice(self.youth_emojis[category])
        return ""


# Глобальный экземпляр для импорта в приложении
style_service = StyleService()
