"""
Тест подключения к DSP API
Простая проверка работоспособности API клиента
"""
from data_layer import DSPClient
import sys


def test_api_connection():
    """Тест подключения к DSP API"""
    
    print("\n" + "="*60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К DSP API")
    print("="*60)
    
    try:
        # Создание клиента
        print("\n[1/5] Создание клиента...")
        client = DSPClient()
        print("[OK] Клиент создан")
        
        # Проверка конфигурации
        print("\n[2/5] Проверка конфигурации...")
        from data_layer import API_BASE
        print(f"  API URL: {API_BASE}")
        masked = '*' * 20 + '...' + client.secret_key[-4:] if client.secret_key and len(client.secret_key) > 4 else 'НЕ НАСТРОЕН'
        print(f"  Secret Key: {masked}")
        print(f"  Client ID: {client.client_id or 'не указан'}")
        
        # Проверка подключения
        print("\n[3/5] Тест подключения...")
        if client.test_connection():
            print("[OK] Подключение успешно!")
        else:
            print("[!] Ошибка подключения")
            return False
        
        # Тест получения данных
        print("\n[4/5] Тест загрузки данных...")
        print("  Загрузка данных за последние 7 дней...")
        
        df = client.get_last_n_days(days=7)
        
        if not df.empty:
            print(f"[OK] Загружено {len(df)} строк")
            print(f"\n  Колонки: {', '.join(df.columns.tolist()[:5])}...")
            print(f"  Первая запись:")
            for col in df.columns[:5]:
                print(f"    - {col}: {df[col].iloc[0]}")
        else:
            print("[!] Нет данных (возможно, пустая база за этот период)")
        
        # Финальный результат
        print("\n[5/5] Итоговая проверка...")
        print("[OK] Все тесты пройдены!")
        print("\n" + "="*60)
        print("DSP API ГОТОВ К ИСПОЛЬЗОВАНИЮ")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n[!] ОШИБКА: {e}")
        print("\nВозможные причины:")
        print("  1. Не настроен .env файл")
        print("  2. Неверный API key")
        print("  3. Неверный API URL")
        print("  4. API недоступен")
        
        print("\nРешение:")
        print("  1. Создайте .env файл: cp .env.example .env")
        print("  2. Заполните DSP_CLIENT_ID и DSP_SECRET_KEY")
        print("  3. См. документацию: API_SETUP.md")
        
        return False


if __name__ == '__main__':
    success = test_api_connection()
    sys.exit(0 if success else 1)

