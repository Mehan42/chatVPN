# Аудит и выбор AI модели для XVPN оркестратора

## Требования к модели
- **Open-source**: свободно распространяемая модель
- **Малый размер**: для установки на серверы с ограниченными ресурсами
- **Docker-совместимость**: должна легко интегрироваться в Docker-контейнеры
- **Оптимизация для минимального стека**: легковесная, но эффективная
- **Аналог TinyLlama**: должна быть сопоставима по производительности

## Анализ доступных моделей

### 1. TinyLlama 1.1B
**Источники**: 
- Hugging Face: https://huggingface.co/TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T
- GitHub: https://github.com/TinyLlama/TinyLlama

**Характеристики**:
- Параметры: 1.1B
- Размер: ~2.2GB (GGUF), ~6.2GB (PyTorch)
- RAM при запуске: 4-6GB
- Оптимизированные форматы: GGUF, safetensors
- Поддержка: CPU, GPU (CUDA)

**Преимущества**:
- Очень маленький размер для 1B модели
- Быстрая загрузка и инференс
- Хорошо оптимизирована для CPU
- Активное сообщество
- Легко интегрируется с Ollama

### 2. Phi-2 2.7B
**Источники**:
- Hugging Face: https://huggingface.co/microsoft/phi-2
- Microsoft Research

**Характеристики**:
- Параметры: 2.7B
- Размер: ~5.1GB
- RAM при запуске: 8-10GB
- Требует больше ресурсов

**Недостатки**:
- Больше требований к ресурсам
- Медленнее инференс

### 3. Mistral 7B (квантованая)
**Источники**:
- Hugging Face: https://huggingface.co/mistralai/Mistral-7B-v0.1
- Версии с квантованием: TheBloke/Mistral-7B-v0.1-GGUF

**Характеристики**:
- Параметры: 7B
- Размер (квант.): ~4.1GB (Q4_K_M)
- RAM при запуске: 6-8GB

**Недостатки**:
- Больше размера и требований к ресурсам
- Требует больше VRAM для GPU

### 4. Qwen 1.5B
**Источники**:
- Hugging Face: https://huggingface.co/Qwen/Qwen1.5-1.8B
- Alibaba DAMO Academy

**Характеристики**:
- Параметры: 1.8B
- Размер: ~3.5GB
- RAM при запуске: 5-7GB

**Недостатки**:
- Больше TinyLlama по размеру

### 5. Gemma 2B
**Источники**:
- Hugging Face: https://huggingface.co/google/gemma-2b
- Google

**Характеристики**:
- Параметры: 2B
- Размер: ~2.5GB
- RAM при запуске: 4-6GB

**Недостатки**:
- Требует больше ресурсов чем TinyLlama

## Рекомендация: TinyLlama 1.1B

### Почему TinyLlama?
1. **Оптимальный размер**: всего ~2.2GB в формате GGUF
2. **Низкие требования к ресурсам**: 4-6GB RAM
3. **Быстрый инференс**: подходит для реального времени
4. **Отличная интеграция**: легко работает с Ollama, llama.cpp
5. **Документация и поддержка**: активное сообщество
6. **Docker-совместимость**: есть готовые образы

### Альтернатива: TinyLlama 1.1B Chat
Для задач оркестрации лучше использовать версию с инструкциями:
- TinyLlama-1.1B-Chat-v1.0
- Тренирована для диалоговых задач
- Лучше понимает контекст управления системой

## Конфигурация для XVPN оркестратора

### 1. Docker-образ с Ollama
```dockerfile
FROM ollama/ollama:latest

# Установка TinyLlama
RUN ollama pull tinyllama:1.1b-chat

# Создание конфигурации
RUN echo 'model: tinyllama:1.1b-chat' > /config/ollama_config.yaml

# Открытие порта
EXPOSE 11434

# Запуск Ollama
CMD ["ollama", "serve"]
```

### 2. Конфигурация orchestrator_config.json
```json
{
  "ai_model": {
    "provider": "ollama",
    "model_name": "tinyllama:1.1b-chat",
    "api_base": "http://localhost:11434",
    "max_tokens": 500,
    "temperature": 0.1,
    "timeout": 30
  }
}
```

### 3. Альтернатива через OpenRouter
Если требуется более мощная модель:

```json
{
  "ai_model": {
    "provider": "openrouter",
    "model_name": "anthropic/claude-haiku",
    "api_base": "https://openrouter.ai/api/v1",
    "max_tokens": 1000,
    "temperature": 0.1,
    "timeout": 60,
    "api_key": "${OPENROUTER_API_KEY}"
  }
}
```

### 4. Ручная установка через llama.cpp
```bash
# Клонируем llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Компиляция
make

# Загрузка модели
wget https://huggingface.co/TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T/resolve/main/tinyllama-1.1b-chat.Q4_K_M.gguf

# Запуск модели
./main -m tinyllama-1.1b-chat.Q4_K_M.gguf -p "Твой запрос" -n 256 --temp 0.1
```

## Сравнение моделей

| Модель | Параметры | Размер | RAM | Производительность | Рекомендация |
|--------|-----------|---------|-----|-------------------|-------------|
| TinyLlama 1.1B | 1.1B | ~2.2GB | 4-6GB | ★★★★★ | **Лучший выбор** |
| Phi-2 2.7B | 2.7B | ~5.1GB | 8-10GB | ★★★★☆ | Альтернатива |
| Mistral 7B Q4 | 7B | ~4.1GB | 6-8GB | ★★★★☆ | Требует больше ресурсов |
| Qwen 1.5B | 1.8B | ~3.5GB | 5-7GB | ★★★★☆ | Средний вариант |
| Gemma 2B | 2B | ~2.5GB | 4-6GB | ★★★★☆ | Альтернатива |

## Заключение

**TinyLlama 1.1B** - оптимальный выбор для XVPN оркестратора:

1. **Минимальные требования**: подходит для слабых серверов
2. **Быстрая интеграция**: легко ставится через Docker
3. **Хорошая производительность**: достаточно для задач оркестрации
4. **Open-source**: свободно распространяемая
5. **Активное развитие**: постоянно улучшается

Для продакшена можно рассмотреть квантованную версию (Q4_K_M) для лучшей производительности.