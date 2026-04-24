# AI Factory - Software Development System

Локальная система полного цикла разработки ПО с ИИ-управлением.

## Возможности

- **5 специализированных агентов**: Planner, Coder, Tester, Debug, Researcher
- **Поддержка локальных LLM**: Ollama (Mistral, CodeQwen)
- **Облачные API**: OpenAI, Anthropic, Google, Groq
- **Task Queue**: асинхронная очередь задач
- **Мониторинг**: логи + метрики + health check
- **Отказоустойчивость**: fallback режим, retry с backoff

## Быстрый старт

### 1. Установка зависимостей

```bash
cd ai-factory
uv sync
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и добавьте API ключи:

```bash
cp .env.example .env
```

### 3. Запуск (без LLM - fallback режим)

```bash
source .venv/bin/activate
python run.py
```

### 4. Запуск с Ollama

```bash
# Скачать и запустить Ollama
ollama serve
ollama pull mistral

# Запуск системы
python run.py
```

## Использование

### Простая задача

```python
from agents.main import MainOrchestrator
import asyncio

async def main():
    orch = MainOrchestrator()
    await orch.start()
    
    # Выполнить задачу
    result = await orch.execute_task(
        "Создай hello world на Python",
        "HelloWorld",
        "coder"
    )
    print(result)
    
    await orch.stop()

asyncio.run(main())
```

### Полный workflow

```python
result = await orch.run_workflow("Создай калькулятор на Python")
```

## Конфигурация

Настройки в `configs/config.yaml`:

- `ollama.host` - адрес Ollama сервера
- `agents.max_concurrent` - максимум параллельных агентов
- `logging.level` - уровень логирования
- `tokens.daily_limit` - дневной лимит токенов

## API адаптеры

Система автоматически выбирает лучший API для задачи:

| Тип задачи | Приоритет API |
|-----------|--------------|
| coding | groq → anthropic → openai |
| reasoning | anthropic → openai → google |
| fast | groq → openai → google |
| general | любой доступный |

## Структура проекта

```
ai-factory/
├── agents/          # Агенты
│   └── main.py
├── configs/         # Конфигурация
│   └── config.yaml
├── logs/           # Логи
├── utils/          # Утилиты
│   ├── adapters.py
│   ├── config.py
│   ├── logger.py
│   ├── monitor.py
│   └── queue.py
└── run.py          # Точка входа
```

## Атрибуты качества

- ✅ Система запускается одним скриптом
- ✅ Fallback режим при недоступности LLM
- ✅ Логирование в файл с timestamp
- ✅ Счетчик токенов
- ✅ Hot-reload конфигурации
- ✅ Health check endpoint (порт 8080)

## Требования

- Python 3.12+
- RAM: 8GB+ (рекомендуется 16GB)
- Ollama (опционально)
- API ключи облачных провайдеров (опционально)