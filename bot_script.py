from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

import pandas as pd

from production.memory_based import user_prediction

# Загружаем датасеты с названиями фильмов
movies_df = pd.read_csv('ml-latest-small/movies.csv')


# Функция для получения топ-N фильмов по жанру

def get_top_n_by_genre(predictions, genre, start=0, n=10):
    # Считаем средний рейтинг для каждого фильма по всем пользователям
    mean_ratings = predictions.mean(axis=0)
    # Фильтруем фильмы по жанру
    genre_movies = movies_df[movies_df['genres'].str.contains(genre, na=False)].copy()
    genre_movies['movieId'] = genre_movies['movieId'] - 1  # Учитываем смещение индекса
    movies_with_ratings = []
    for _, row in genre_movies.iterrows():
        movie_id = int(row['movieId'])
        if movie_id < len(mean_ratings):  # Проверяем, что movie_id существует в predictions
            title = row['title']
            avg_rating = mean_ratings[movie_id]
            movies_with_ratings.append((title, avg_rating))

    # Сортируем фильмы по рейтингу
    movies_with_ratings = sorted(movies_with_ratings, key=lambda x: x[1], reverse=True)
    return [f"{i + 1 + start}. {title} - Rating: {rating:.2f}" for i, (title, rating) in
            enumerate(movies_with_ratings[start:start + n])]


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    greeting_message = (
        "Здравствуйте! Это рекомендательная система фильмов. "
        "Вы хотите продолжить? "
    )
    keyboard = [[InlineKeyboardButton("Продолжить", callback_data="continue")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(greeting_message, reply_markup=reply_markup)


# Обработчик для продолжения
async def continue_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    genre_message = "Пожалуйста, выберите основной жанр фильма. "
    genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Fantasy", "Horror", "Musical",
              "Thriller"]
    keyboard = [[InlineKeyboardButton(genre, callback_data=f"genre:{genre}")] for genre in genres]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(genre_message, reply_markup=reply_markup)


# Обработчик выбора жанра
async def genre_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    genre = query.data.split(":")[1]

    # Сохраняем жанр и начальный индекс в контексте пользователя
    context.user_data["genre"] = genre
    context.user_data["start_index"] = 0

    # Получаем топ-10 фильмов выбранного жанра
    top_movies = get_top_n_by_genre(user_prediction, genre, start=0, n=10)
    top_movies_message = f"Топ-10 фильмов в жанре '{genre}':\n\n" + "\n".join(top_movies)

    keyboard = [
        [InlineKeyboardButton("Вернуться", callback_data="continue"),
         InlineKeyboardButton("Остаться", callback_data="stay"),
         InlineKeyboardButton("Следующий", callback_data="next")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(top_movies_message, reply_markup=reply_markup)


# Обработчик кнопки "Остаться"
async def stay_top_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    genre = context.user_data.get("genre", "")
    start_index = context.user_data.get("start_index", 0)

    top_movies = get_top_n_by_genre(user_prediction, genre, start=start_index, n=10)
    top_movies_message = f"Топ-10 фильмов в жанре '{genre}':\n\n" + "\n".join(top_movies)
    top_movies_message += "\n\nПриятного вечера за просмотром данных фильмов!"

    await query.answer()
    await query.edit_message_text(top_movies_message)


# Обработчик кнопки "Не нравится"
async def next_top_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    genre = context.user_data.get("genre", "")
    start_index = context.user_data.get("start_index", 0) + 10

    # Сохраняем новый стартовый индекс
    context.user_data["start_index"] = start_index

    top_movies = get_top_n_by_genre(user_prediction, genre, start=start_index, n=10)
    top_movies_message = f"Топ-10 фильмов в жанре '{genre}':\n\n" + "\n".join(top_movies)

    keyboard = [
        [InlineKeyboardButton("Вернуться", callback_data="continue"),
         InlineKeyboardButton("Остаться", callback_data="stay"),
         InlineKeyboardButton("Следующий", callback_data="next")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(top_movies_message, reply_markup=reply_markup)


# Основная программа
def main():
    application = ApplicationBuilder().token('7335732776:AAH60K1pKsT3m1VPAXNAzxMOJrerG4Ve6Cc').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(continue_selection, pattern="^continue$"))
    application.add_handler(CallbackQueryHandler(genre_selection, pattern="^genre:.*$"))
    application.add_handler(CallbackQueryHandler(stay_top_movies, pattern="^stay$"))
    application.add_handler(CallbackQueryHandler(next_top_movies, pattern="^next$"))
    application.run_polling()

if __name__ == "__main__":
    main()