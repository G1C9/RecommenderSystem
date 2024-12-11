from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

import pandas as pd

from production.memory_based import user_prediction

# Загружаем датасеты с названиями фильмов и ссылками на IMDb
movies_df = pd.read_csv('ml-latest-small/movies.csv')
links_df = pd.read_csv('ml-latest-small/links.csv')

# Объединяем movies_df и links_df по movieId
movies_with_links_df = pd.merge(movies_df, links_df, on='movieId')

# Функция для получения топ-10 фильмов с названиями и ссылками по жанру
def get_top_n_by_genre(predictions, genre, n=10):
    # Считаем средний рейтинг для каждого фильма по всем пользователям
    mean_ratings = predictions.mean(axis=0)
    # Фильтруем фильмы по жанру
    genre_movies = movies_with_links_df[movies_with_links_df['genres'].str.contains(genre, na=False)].copy()
    # Находим индексы фильмов из указанного жанра и создаем копию DataFrame
    genre_movies['movieId'] = genre_movies['movieId'] - 1  # Учитываем смещение индекса
    top_movies = []
    count = 0
    for _, row in genre_movies.iterrows():
        movie_id = int(row['movieId'])
        if movie_id < len(mean_ratings):  # Проверяем, что movie_id существует в predictions
            title = row['title']
            avg_rating = mean_ratings[movie_id]
            imdb_id = str(row['imdbId']).zfill(7)  # Преобразуем imdbId в строку
            imdb_link = f"https://www.imdb.com/title/tt{imdb_id}/"  # Формируем правильную ссылку на IMDb
            top_movies.append((title, avg_rating, imdb_link))
            count += 1
        if count == n:
            break

    # Сортируем фильмы по рейтингу и берем топ-N
    top_movies = sorted(top_movies, key=lambda x: x[1], reverse=True)[:n]
    return [f"{i + 1}. {title} - Rating: {rating:.2f} - IMDb: {imdb_link}" for i, (title, rating, imdb_link) in enumerate(top_movies)]

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Текст приветствия
    greeting_message = (
        "Здравствуйте! Это рекомендательная система фильмов до 2010 года. "
        "Пожалуйста, выберите основной жанр фильма."
    )
    # Создаем кнопки для выбора жанра
    genres = ["Adventure", "Drama", "Fantasy", "Comedy"]
    keyboard = [[InlineKeyboardButton(genre, callback_data=genre)] for genre in genres]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с кнопками
    await update.message.reply_text(greeting_message, reply_markup=reply_markup)

# Обработчик выбора жанра
async def genre_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получаем выбранный жанр из callback_data
    query = update.callback_query
    genre = query.data

    # Получаем топ-10 фильмов выбранного жанра
    top_movies = get_top_n_by_genre(user_prediction, genre, n=10)
    top_movies_message = f"Топ-10 фильмов в жанре '{genre}':\n\n" + "\n".join(top_movies)

    # Редактируем сообщение с кнопками и отправляем результат
    await query.answer()
    await query.edit_message_text(top_movies_message)

# Основная программа
def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    application = ApplicationBuilder().token('7335732776:AAH60K1pKsT3m1VPAXNAzxMOJrerG4Ve6Cc').build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(genre_selection))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
