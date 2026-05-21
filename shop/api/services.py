import requests
import logging

logger = logging.getLogger(__name__)

def get_random_fact():
    """Получение случайного факта из API"""
    try:
        response = requests.get('https://uselessfacts.jsph.pl/random.json?language=en', timeout=5)
        if response.status_code == 200:
            return response.json().get('text', 'Интересный факт о сладостях...')
    except Exception as e:
        logger.error(f"Ошибка получения факта: {e}")
    return "Шоколад полезен для сердца в умеренных количествах!"

def get_joke():
    """Получение случайной шутки из API"""
    try:
        response = requests.get('https://v2.jokeapi.dev/joke/Any?safe-mode', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['type'] == 'single':
                return data['joke']
            else:
                return f"{data['setup']} - {data['delivery']}"
    except Exception as e:
        logger.error(f"Ошибка получения шутки: {e}")
    return "Почему кондитеры такие счастливые? Потому что у них всегда есть запасной торт!"