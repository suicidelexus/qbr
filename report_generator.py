"""
Report Generator - генерация отчетов
"""
from typing import Dict, List
import json


class ReportGenerator:
    """Генератор отчетов"""
    
    def __init__(self, analysis_results: Dict):
        self.results = analysis_results
    
    def generate_markdown(self) -> str:
        """Генерация Markdown отчета"""
        md = []
        
        # Title
        md.append("# DSP Analytics Report\n")
        
        # TL;DR
        md.append("## TL;DR\n")
        md.append(self.results['tldr'])
        md.append("\n")
        
        # Key Insights
        md.append("## Ключевые инсайты\n")
        all_insights = (
            self.results['advertisers']['insights'] +
            self.results['products']['insights'] +
            self.results['media_split']['insights'] +
            self.results['dynamics']['insights'] +
            self.results['dmp']['insights'] +
            self.results['frequency']['insights'] +
            self.results['conversions']['insights']
        )
        for insight in all_insights:
            md.append(f"- {insight}\n")
        md.append("\n")
        
        # Advertisers
        md.append("## Сравнение Advertisers\n")
        for insight in self.results['advertisers']['insights']:
            md.append(f"- {insight}\n")
        md.append("\n")
        
        # Products
        md.append("## Сравнение продуктов\n")
        for insight in self.results['products']['insights']:
            md.append(f"- {insight}\n")
        md.append("\n")
        
        # Media Split
        md.append("## Медиасплит\n")
        for insight in self.results['media_split']['insights']:
            md.append(f"- {insight}\n")
        md.append("\n")
        
        # Dynamics
        md.append("## Динамика\n")
        for insight in self.results['dynamics']['insights']:
            md.append(f"- {insight}\n")
        md.append("\n")
        
        # DMP
        md.append("## DMP Анализ\n")
        for insight in self.results['dmp']['insights']:
            md.append(f"- {insight}\n")
        md.append("\n")
        
        # Frequency
        md.append("## Frequency Анализ\n")
        for insight in self.results['frequency']['insights']:
            md.append(f"- {insight}\n")
        md.append("\n")
        
        # Conversions
        if self.results['conversions']['insights']:
            md.append("## Конверсионный анализ\n")
            for insight in self.results['conversions']['insights']:
                md.append(f"- {insight}\n")
            md.append("\n")
        
        # Correlation
        if self.results.get('correlation', {}).get('insights'):
            md.append("## Корреляционный анализ\n")
            for insight in self.results['correlation']['insights']:
                md.append(f"- {insight}\n")
            md.append("\n")
        
        # Budget Optimization
        if self.results.get('budget_optimization', {}).get('insights'):
            md.append("## Оптимизация бюджета\n")
            for insight in self.results['budget_optimization']['insights']:
                md.append(f"- {insight}\n")
            md.append("\n")
        
        # Recommendations
        md.append("## Рекомендации\n")
        for i, rec in enumerate(self.results['recommendations'], 1):
            md.append(f"{i}. {rec}\n")
        md.append("\n")
        
        # Hypotheses
        md.append("## Гипотезы для тестирования\n")
        for hyp in self.results['hypotheses']:
            md.append(f"- {hyp}\n")
        md.append("\n")
        
        return "".join(md)
    
    def generate_slides_structure(self) -> List[Dict]:
        """Генерация структуры для Google Slides"""
        slides = []
        
        # 1. Title
        slides.append({
            'type': 'title',
            'title': 'DSP Analytics Report',
            'subtitle': 'Quarterly Business Review'
        })
        
        # 2. TL;DR
        slides.append({
            'type': 'content',
            'title': 'TL;DR',
            'content': self.results['tldr']
        })
        
        # 3. Advertisers
        slides.append({
            'type': 'content_chart',
            'title': 'Сравнение Advertisers',
            'insights': self.results['advertisers']['insights'],
            'chart': 'advertisers'
        })
        
        # 4. Products
        slides.append({
            'type': 'content_chart',
            'title': 'Сравнение продуктов',
            'insights': self.results['products']['insights'],
            'chart': 'products'
        })
        
        # 5. Media Split
        slides.append({
            'type': 'content_chart',
            'title': 'Медиасплит',
            'insights': self.results['media_split']['insights'],
            'chart': 'media_split'
        })
        
        # 6. Performance
        slides.append({
            'type': 'content',
            'title': 'Performance Overview',
            'insights': self.results['advertisers']['insights'][:3]
        })
        
        # 7. Dynamics
        slides.append({
            'type': 'content_chart',
            'title': 'Динамика',
            'insights': self.results['dynamics']['insights'],
            'chart': 'dynamics'
        })
        
        # 8. DMP
        slides.append({
            'type': 'content_chart',
            'title': 'DMP Анализ',
            'insights': self.results['dmp']['insights'],
            'chart': 'dmp'
        })
        
        # 9. Frequency
        slides.append({
            'type': 'content',
            'title': 'Frequency Анализ',
            'insights': self.results['frequency']['insights']
        })
        
        # 10. Recommendations
        slides.append({
            'type': 'content',
            'title': 'Рекомендации',
            'content': self.results['recommendations']
        })
        
        # 11. Hypotheses
        slides.append({
            'type': 'content',
            'title': 'Гипотезы',
            'content': self.results['hypotheses']
        })
        
        return slides
    
    def save_json(self, filepath: str):
        """Сохранение результатов в JSON"""
        # Конвертация DataFrame в dict для сериализации
        output = {}
        for key, value in self.results.items():
            if isinstance(value, dict):
                output[key] = {}
                for k, v in value.items():
                    if hasattr(v, 'to_dict'):
                        output[key][k] = v.to_dict('records')
                    else:
                        output[key][k] = v
            else:
                output[key] = value
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    
    def save_markdown(self, filepath: str):
        """Сохранение Markdown отчета"""
        content = self.generate_markdown()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

