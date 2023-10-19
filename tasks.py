import os
from celery import Celery
from torch.distributed._tensor.ops import DimSpec
# Импортируем необходимые библиотеки
from transformers import AutoTokenizer, AutoModel
import torch

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from aiogram import Bot
import asyncio

REDIS_HOST='185.17.141.230'
REDIS_PORT=6379

app = Celery("tasks")
app.conf.broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
app.conf.result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

async def send_answer(token, user_id, answer):
    bot = Bot(token)
    await bot.send_message(user_id, answer)

@app.task
def simple_task(token, user_id, description):
    # description_bd = pd.read_csv('answers.csv')
    # description = description_bd['message'][0]

    df = pd.read_csv("movies_metadata.csv", low_memory=False)

    similar = []  # массив, который содержит оценку схожести двух описаний

    accuracy = 0.6
    amount_rows = 300
    stop_flag_len = 20

    for i, x in enumerate(df["overview"]):
        if i >= amount_rows:
            break
        overview = f"{x}"  # описание фильма из датасета
        # Инициализируем нашу модель высокочастотного трансформатора (HF transformer model) и токенизатор - используя предварительно обученную модель SBERT.
        tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/bert-base-nli-mean-tokens')
        model = AutoModel.from_pretrained('sentence-transformers/bert-base-nli-mean-tokens')
        # Токенизируем предложения
        tokens = tokenizer([overview, description],
                           max_length=128,
                           truncation=True,
                           padding='max_length',
                           return_tensors='pt')
        # Обрабатываем наши токенизированные тензоры с помощью модели
        outputs = model(**tokens)
        # Здесь последний слой эмбеддингов, last_hidden_state
        embeddings = outputs.last_hidden_state
        # создание masking array, умножаем каждое значение в тензоре embeddings на соответствующее значение attention_mask
        mask = tokens['attention_mask'].unsqueeze(-1).expand(embeddings.size()).float()
        # Masking array имеет форму, аналогичную выходным embeddings - мы их перемножаем
        masked_embeddings = embeddings * mask
        # Суммируем оставшиеся embeddings
        summed = torch.sum(masked_embeddings, 1)
        # Подсчитываем количество значений, которым следует уделить внимание в каждой позиции тензора
        counted = torch.clamp(mask.sum(1), min=1e-9)
        # Получаем mean-pooled значения в качестве суммы эмбеддингов
        mean_pooled = summed / counted
        # конвертируем numpy array из torch tensor
        mean_pooled = mean_pooled.detach().numpy()
        # вычисляем степень схожести (будет сохранена в массиве)
        scores = np.zeros((mean_pooled.shape[0], mean_pooled.shape[0]))
        for i in range(mean_pooled.shape[0]):
            scores[i, :] = cosine_similarity(
                [mean_pooled[i]],
                mean_pooled
            )[0]
        similarity_scores = scores[0, 1]  # берём необходимое значение схожести
        idx = df.index[df['overview'] == overview].tolist()
        # выбираем порог, выше которого описания будут считаться похожими друг на друга
        if similarity_scores > accuracy:
            similar.append(similarity_scores)
            titles = df["title"].iloc[idx].to_numpy()
            
        if len(similar) == stop_flag_len:  # выбираем желаемое количество результатов
            break

    # description_bd = description_bd.drop([0])
    answer = str(titles[0]) + " - " + str(x) # выводим назвнания фильмов из датасета, которые удовлетворяют установленной точности
    coro = send_answer(token, user_id, answer)
    asyncio.run(coro)
    return (answer, similarity_scores)


app.conf.task_routes = {
    'simple_task': {'queue': 'main_queue'},
}