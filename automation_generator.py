"""
Automation Code Generator
Генерация кода для автоматизации сбора и анализа данных
"""
from typing import List, Dict
from datetime import datetime


class AutomationGenerator:
    """Генератор кода для автоматизации"""
    
    @staticmethod
    def generate_scheduler_script(
        credentials: List[Dict],
        schedule_type: str = 'daily',
        output_dir: str = './reports'
    ) -> str:
        """
        Генерация скрипта для планировщика
        
        Args:
            credentials: список credentials advertisers
            schedule_type: тип расписания (daily, weekly, monthly)
            output_dir: папка для отчетов
        
        Returns:
            Python код скрипта
        """
        # Формируем credentials list
        creds_str = "[\n"
        for cred in credentials:
            creds_str += f"    {{\n"
            creds_str += f"        'advertiser': '{cred['advertiser']}',\n"
            creds_str += f"        'client_id': '{cred.get('client_id', 'YOUR_CLIENT_ID')}',\n"
            creds_str += f"        'secret_key': '{cred.get('secret_key', 'YOUR_SECRET_KEY')}',\n"
            creds_str += f"    }},\n"
        creds_str += "]"
        
        script = f'''#!/usr/bin/env python3
"""
Автоматический сбор и анализ данных DSP
Генерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
import sys
import os
from datetime import datetime, timedelta
import logging

# Настройка путей
sys.path.append(os.path.dirname(__file__))

from multi_advertiser import MultiAdvertiserManager
from analytics_agent import AnalyticsAgent
from report_generator import ReportGenerator
from visualization import ChartGenerator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_analysis():
    """Основная функция анализа"""
    logger.info("="*60)
    logger.info("ЗАПУСК АВТОМАТИЧЕСКОГО АНАЛИЗА")
    logger.info("="*60)
    
    # 1. Настройка credentials
    credentials = {creds_str}
    
    # 2. Создание менеджера
    logger.info("Инициализация менеджера...")
    manager = MultiAdvertiserManager(credentials=credentials)
    
    # 3. Определение периода
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)  # За последнюю неделю
    
    logger.info(f"Период: {{start_date}} - {{end_date}}")
    
    # 4. Загрузка данных
    logger.info("Загрузка данных...")
    df = manager.load_data(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        parallel=True
    )
    
    if df.empty:
        logger.error("Нет данных для анализа")
        return False
    
    logger.info(f"Загружено {{len(df)}} строк")
    
    # 5. Валидация данных
    logger.info("Валидация данных...")
    validation = manager.validate_data_compatibility(df)
    logger.info(f"Статус валидации: {{validation['status']}}")
    
    if validation['issues']:
        logger.warning("Проблемы с данными:")
        for issue in validation['issues']:
            logger.warning(f"  - {{issue}}")
    
    # 6. AI-анализ
    logger.info("Запуск AI-анализа...")
    agent = AnalyticsAgent(df)
    results = agent.auto_analyze()
    
    logger.info(f"Найдено {{len(results.get('opportunities', []))}} возможностей оптимизации")
    logger.info(f"Сгенерировано {{len(results.get('additional_questions', []))}} вопросов")
    
    # 7. Генерация отчета
    logger.info("Генерация отчета...")
    output_dir = "{output_dir}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Markdown отчет
    report_gen = ReportGenerator(results)
    report_path = os.path.join(output_dir, f"report_{{end_date}}.md")
    report_gen.save_to_file(report_path)
    logger.info(f"Отчет сохранен: {{report_path}}")
    
    # 8. Генерация графиков
    logger.info("Генерация графиков...")
    chart_gen = ChartGenerator()
    charts_dir = os.path.join(output_dir, 'charts')
    chart_gen.generate_all_charts(results, output_dir=charts_dir)
    logger.info(f"Графики сохранены в {{charts_dir}}")
    
    # 9. Сводка по advertisers
    logger.info("\\nСводка по advertisers:")
    summary = manager.get_comparison_summary(df)
    for _, row in summary.iterrows():
        logger.info(f"  {{row['advertiser_source']}}: CTR={{row['ctr']:.3%}}, Spend={{row['TotalSum']:,.0f}}")
    
    logger.info("="*60)
    logger.info("АНАЛИЗ ЗАВЕРШЕН УСПЕШНО")
    logger.info("="*60)
    
    return True


if __name__ == '__main__':
    try:
        success = run_analysis()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {{e}}", exc_info=True)
        sys.exit(1)
'''
        
        return script
    
    @staticmethod
    def generate_cron_config(schedule_type: str = 'daily') -> str:
        """
        Генерация cron конфигурации
        
        Args:
            schedule_type: тип расписания
        
        Returns:
            Cron строка
        """
        schedules = {
            'daily': '0 9 * * *',      # Каждый день в 9:00
            'weekly': '0 9 * * 1',     # Каждый понедельник в 9:00
            'monthly': '0 9 1 * *',    # 1-го числа каждого месяца в 9:00
            'hourly': '0 * * * *'      # Каждый час
        }
        
        cron_line = schedules.get(schedule_type, schedules['daily'])
        script_path = '/path/to/your/automation_script.py'
        python_path = '/usr/bin/python3'
        
        config = f'''# Cron configuration for DSP Analytics Automation
# Schedule: {schedule_type}

# Format: минута час день месяц день_недели команда

{cron_line} {python_path} {script_path} >> /var/log/dsp_analytics.log 2>&1

# To install:
# 1. Edit cron: crontab -e
# 2. Add the line above
# 3. Save and exit
# 4. Verify: crontab -l
'''
        return config
    
    @staticmethod
    def generate_docker_compose(
        credentials: List[Dict],
        schedule: str = 'daily'
    ) -> str:
        """
        Генерация docker-compose.yml для контейнеризации
        
        Args:
            credentials: список credentials
            schedule: расписание
        
        Returns:
            docker-compose.yml содержимое
        """
        compose = f'''version: '3.8'

services:
  dsp-analytics:
    build: .
    container_name: dsp-analytics-automation
    environment:
      - SCHEDULE_TYPE={schedule}
      - TZ=Europe/Moscow
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
    restart: unless-stopped
    command: python automation_script.py

  # Опционально: база данных для хранения результатов
  # postgres:
  #   image: postgres:14
  #   container_name: dsp-analytics-db
  #   environment:
  #     POSTGRES_DB: dsp_analytics
  #     POSTGRES_USER: admin
  #     POSTGRES_PASSWORD: changeme
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

# volumes:
#   postgres_data:
'''
        return compose
    
    @staticmethod
    def generate_dockerfile() -> str:
        """
        Генерация Dockerfile
        
        Returns:
            Dockerfile содержимое
        """
        dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем папки для вывода
RUN mkdir -p /app/reports /app/logs

CMD ["python", "automation_script.py"]
'''
        return dockerfile
    
    @staticmethod
    def generate_github_actions_workflow(
        credentials: List[Dict],
        schedule: str = 'daily'
    ) -> str:
        """
        Генерация GitHub Actions workflow
        
        Args:
            credentials: список credentials
            schedule: расписание (daily, weekly, etc.)
        
        Returns:
            YAML содержимое workflow
        """
        schedules_cron = {
            'daily': '0 9 * * *',
            'weekly': '0 9 * * 1',
            'monthly': '0 9 1 * *'
        }
        
        cron = schedules_cron.get(schedule, '0 9 * * *')
        
        workflow = f'''name: DSP Analytics Automation

on:
  schedule:
    - cron: '{cron}'  # {schedule}
  workflow_dispatch:  # Ручной запуск

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run analysis
      env:
        # Добавьте API ключи в GitHub Secrets
'''
        
        for i, cred in enumerate(credentials, 1):
            workflow += f"        API_KEY_{i}: ${{{{ secrets.API_KEY_{i} }}}}\n"
        
        workflow += '''      run: |
        python automation_script.py
    
    - name: Upload reports
      uses: actions/upload-artifact@v3
      with:
        name: dsp-reports
        path: reports/
    
    # Опционально: отправка в Slack/Email
    # - name: Notify
    #   run: |
    #     # Ваш код уведомления
'''
        return workflow
    
    @staticmethod
    def generate_readme_automation() -> str:
        """
        Генерация README для автоматизации
        
        Returns:
            Markdown документация
        """
        readme = '''# DSP Analytics Automation

Автоматический сбор и анализ данных из нескольких DSP advertisers.

## Быстрый старт

### 1. Настройка credentials

Отредактируйте `automation_script.py`:
```python
credentials = [
    {"advertiser": "Advertiser A", "api_key": "your_key_1"},
    {"advertiser": "Advertiser B", "api_key": "your_key_2"},
]
```

### 2. Локальный запуск

```bash
python automation_script.py
```

### 3. Автоматизация

#### Вариант A: Cron (Linux/Mac)

```bash
# Открыть crontab
crontab -e

# Добавить строку (каждый день в 9:00)
0 9 * * * /usr/bin/python3 /path/to/automation_script.py
```

#### Вариант B: Task Scheduler (Windows)

1. Открыть Task Scheduler
2. Create Basic Task
3. Trigger: Daily, 9:00 AM
4. Action: Start a Program
5. Program: `python`
6. Arguments: `/path/to/automation_script.py`

#### Вариант C: Docker

```bash
docker-compose up -d
```

#### Вариант D: GitHub Actions

1. Добавить API ключи в Secrets
2. Workflow запускается автоматически по расписанию

## Структура отчетов

```
reports/
├── report_2024-03-23.md
├── charts/
│   ├── advertisers.html
│   ├── correlation.html
│   └── ...
└── results.json
```

## Логи

Логи сохраняются в `automation.log`

## Мониторинг

Проверить последний запуск:
```bash
tail -f automation.log
```

## Troubleshooting

### Ошибка 401
→ Проверьте API ключи

### Нет данных
→ Проверьте период и статус кампаний

### Timeout
→ Увеличьте timeout в клиенте
'''
        return readme


def generate_full_automation_package(
    credentials: List[Dict],
    output_dir: str = './automation'
) -> Dict[str, str]:
    """
    Генерация полного пакета автоматизации
    
    Args:
        credentials: список credentials
        output_dir: папка для файлов
    
    Returns:
        Словарь {filename: content}
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    generator = AutomationGenerator()
    
    files = {
        'automation_script.py': generator.generate_scheduler_script(credentials),
        'cron_config.txt': generator.generate_cron_config('daily'),
        'docker-compose.yml': generator.generate_docker_compose(credentials),
        'Dockerfile': generator.generate_dockerfile(),
        '.github/workflows/automation.yml': generator.generate_github_actions_workflow(credentials),
        'README_AUTOMATION.md': generator.generate_readme_automation()
    }
    
    # Сохраняем файлы
    for filename, content in files.items():
        filepath = os.path.join(output_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Создан: {filepath}")
    
    return files

