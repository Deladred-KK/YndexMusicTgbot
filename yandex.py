import yandex_music
import telebot
from io import BytesIO
import logging
import time
import os

# Настройка логирования
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#Тег админа
ALLOWED_USER_ID = 1487950361 

# Флаг для отслеживания, может ли бот искать песню
waiting_for_song = False

bot = telebot.TeleBot("Your_token")

# Введите ваш токен для Yandex Music API
client = yandex_music.Client('Token')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global waiting_for_song
    waiting_for_song = True
    logging.info(f"User {message.from_user.id} started the bot.")
    bot.reply_to(message, "Привет! Отправьте название песни, например: 'Название песни'")

@bot.message_handler(func=lambda message: waiting_for_song)
def send_song(message):
    global waiting_for_song
    user_id = message.from_user.id
    track_name = message.text
    logging.info(f"User {user_id} requested song: {track_name}")
    try:
        search_results = client.search(track_name)

        # Проверяем наличие результатов поиска
        if search_results.tracks and hasattr(search_results.tracks, 'results') and search_results.tracks.results:
            track = search_results.tracks.results[0]
            album_id = track.albums[0]['id']
            print(f"ID альбома: {album_id}")
            print(f"ID трека '{track.title}': {track.id}")
            # Получаем информацию о песне
            try:
                track = client.tracks([track.id])[0]
                album = client.albums([album_id])[0]
            except yandex_music.exceptions.YandexMusicError as e:
                print(f"Ошибка при получении данных: {e}")
                exit()
            artist1 = ", ".join([artist.name for artist in track.artists])
            # Форматируем информацию о песне **без пробелов в начале строк**
            song_info = f"""\
Название: <b>{track.title}</b>
Исполнитель: <b>{artist1}</b>
Альбом: <b>{album.title}</b>
Год: <b>{album.year}</b>
Длительность: <b>{track.duration_ms // 1000} секунд</b>
Ссылка: <b>https://music.yandex.ru/album/{album_id}/track/{track.id}</b>
            """

            tracks = client.tracks([f"{track.id}:{album_id}"])
            if tracks:
                track = tracks[0]
                track.download(f"{track.title} - {artist1}.mp3")

                # Отправляем песню и информацию о ней
                bot.send_audio(message.chat.id, audio=open(f'{track.title} - {artist1}.mp3', 'rb'), title=f"{track.title} - {artist1}", caption=song_info, reply_to_message_id=message.message_id, parse_mode='HTML')
                logging.info(f"Sent song '{track.title}' to user {user_id}. URL: https://music.yandex.ru/album/{album_id}/track/{track.id}")
                def remove_files(folder_path):
                  """
                  Удаляет все файлы с расширениями .mp4 и .jpg из указанной папки.
                
                  Args:
                    folder_path: Путь к папке, из которой нужно удалить файлы.
                  """
                  for filename in os.listdir(folder_path):
                    # Проверяем, заканчивается ли имя файла на .mp4 или .jpg
                    if filename.endswith(".mp3") or filename.endswith(".jpg"):
                      # Формируем полный путь к файлу
                      file_path = os.path.join(folder_path, filename)
                      # Удаляем файл
                      os.remove(file_path)
                      print(f"Файл удален: {file_path}")

                # Укажите путь к папке, из которой нужно удалить файлы
                folder_path = "D:/script"

                # Вызов функции для удаления файлов
                remove_files(folder_path)
            else:
                bot.reply_to(message, f"Не удалось найти песню '{track_name}'.")
                logging.info(f"Song '{track_name}' not found for user {user_id}")
        else:
            bot.reply_to(message, f"Не удалось найти песню '{track_name}'.")
            logging.info(f"Song '{track_name}' not found for user {user_id}")

    except telebot.apihelper.ApiException as e:
        logging.error(f"Telegram API error: {e}")
        bot.reply_to(message, "Произошла ошибка Telegram. Попробуйте позже.")
        time.sleep(5)
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при загрузке песни: {e}")
        logging.error(f"Error downloading song for user {user_id}: {e}")
    finally:
        waiting_for_song = False
 
@bot.message_handler(commands=['send_log'])
def send_log_file(message):
    """Отправляет файл логов бота только пользователю с заданным ID."""
    user_id = message.from_user.id
    if user_id == ALLOWED_USER_ID:
        try:
            with open("bot.log", 'rb') as log_file:
                bot.send_document(message.chat.id, log_file, reply_to_message_id=message.message_id, parse_mode='HTML')
                logging.info(f"Sent log file to user {user_id}")
        except FileNotFoundError:
            bot.reply_to(message, "Файл логов не найден.")
            logging.error("Log file not found.")
    else:
        bot.reply_to(message, "У вас нет доступа к этой команде.")
        logging.warning(f"User {user_id} tried to access logs without permission.")
 
@bot.message_handler(func=lambda message: "Сервер/ноутбук запущен!" in message.text)
def handle_server_message(message):
  """Отвечает "Круто, попущь" на сообщение "Сервер/ноутбук запущен!".
  """
  logging.info(f"User {message.from_user.id} sent server start message.")
  bot.send_message(message.chat.id, "Круто, попущь")
 
@bot.message_handler(func=lambda message: "Ноутбук отключён, фриз не ори на меня, бб!" in message.text)
def handle_server_message(message):
  """Отвечает "ЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭ, куда".
  """
  logging.info(f"User {message.from_user.id} sent server shutdown message.")
  bot.send_message(message.chat.id, "ЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭЭ, куда")  

def get_top_3_tracks(artist_name):
    """
    Получает 3 самых популярных трека исполнителя.

    Args:
        artist_name: Имя исполнителя.

    Returns:
        Кортеж из 6 элементов: 
            - Айди трека 1, 
            - Айди альбома трека 1,
            - Айди трека 2, 
            - Айди альбома трека 2,
            - Айди трека 3, 
            - Айди альбома трека 3,
        либо None, если не удалось получить треки.
    """
    print(f"Отладка: Поиск исполнителя '{artist_name}'...")
    search_results = client.search(artist_name, type_='artist')

    if search_results.artists.total > 0:
        print("Отладка: Исполнитель найден.")
        artist = search_results.artists.results[0]
        print(f"Отладка: ID исполнителя: {artist.id}")
        
        print(f"Отладка: Получение всех треков исполнителя...")
        tracks = client.artists_tracks(artist.id)  
        print(f"Отладка: Найдено треков: {len(tracks)}")

        if len(tracks) >= 3:
            track1_id = tracks[0].id
            track1_album_id = tracks[0].albums[0].id
            track2_id = tracks[1].id
            track2_album_id = tracks[1].albums[0].id
            track3_id = tracks[2].id
            track3_album_id = tracks[2].albums[0].id
            return track1_id, track1_album_id, track2_id, track2_album_id, track3_id, track3_album_id
        else:
            print(f"Отладка: У исполнителя меньше 3 треков.")
            return None
    else:
        print("Отладка: Исполнитель не найден.")
        return None

@bot.message_handler(commands=['top3'])
def get_top_3_tracks_command(message):
    """
    Обрабатывает команду /top3 для получения топ-3 треков исполнителя.
    """
    global waiting_for_song
    waiting_for_song = True
    bot.reply_to(message, "Введите имя исполнителя:")

    # Ожидаем ввода имени исполнителя
    bot.register_next_step_handler(message, process_artist_name)

def process_artist_name(message):
    """
    Обрабатывает имя исполнителя и отправляет информацию о топ-3 треках.
    """
    global waiting_for_song
    artist_name = message.text
    logging.info(f"User {message.from_user.id} requested top 3 tracks for artist: {artist_name}")
    top_tracks = get_top_3_tracks(artist_name)

    if top_tracks:
        track1_id, track1_album_id, track2_id, track2_album_id, track3_id, track3_album_id = top_tracks
        
        # Получаем информацию о каждом треке и отправляем ее пользователю
        for i, (track_id, album_id) in enumerate([(track1_id, track1_album_id), (track2_id, track2_album_id), (track3_id, track3_album_id)], start=1):
            try:
                track = client.tracks([track_id])[0]
                album = client.albums([album_id])[0]
                artist1 = ", ".join([artist.name for artist in track.artists])

                song_info = f"""\
Трек {i}:
Название: <b>{track.title}</b>
Исполнитель: <b>{artist1}</b>
Альбом: <b>{album.title}</b>
Год: <b>{album.year}</b>
Длительность: <b>{track.duration_ms // 1000} секунд</b>
Ссылка: <b>https://music.yandex.ru/album/{album_id}/track/{track.id}</b>
                """
                bot.send_message(message.chat.id, song_info, parse_mode='HTML')
            except Exception as e:
                bot.reply_to(message, f"Произошла ошибка при получении информации о треке {i}: {e}")
                logging.error(f"Error getting track information for user {message.from_user.id}: {e}")
    else:
        bot.reply_to(message, f"Не удалось получить треки для исполнителя '{artist_name}'")
        logging.info(f"Could not get tracks for artist '{artist_name}' for user {message.from_user.id}")
    waiting_for_song = False
 
bot.polling()
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Bot polling error: {e}")
        time.sleep(15)
