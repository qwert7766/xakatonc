# recommendations/scorer.py
import math
from profiles.models import Employee


class EmployeeScorer:
    """Класс для оценки соответствия сотрудника идеальному профилю"""
    
    def __init__(self, ideal_profile):
        self.ideal = ideal_profile
        
    def calculate_match_score(self, employee):
        """Рассчитывает общий процент соответствия (0-100)"""
        scores = {
            'disc': self._score_disc(employee) * 0.35,     
            'age': self._score_age(employee) * 0.10,   
            'generation': self._score_generation(employee) * 0.10,
            'gerchikov': self._score_gerchikov(employee) * 0.20,
            'role_functions': self._score_role_functions(employee) * 0.25,
        }
        
        total = sum(scores.values())
        breakdown = {k: round(v * 100, 1) for k, v in scores.items()}
        
        return round(total, 1), breakdown
    
    def _score_disc(self, employee):
        """Оценка DISC-профиля (0-1)"""
        if not employee.disc_scores or not self.ideal.disc_preferred:
            return 0.5
        
        disc_ideal = self.ideal.disc_preferred
        disc_real = employee.disc_scores
        
        dot_product = sum(disc_ideal.get(k, 0) * disc_real.get(k, 0) for k in 'DISC')
        norm_ideal = math.sqrt(sum(v ** 2 for v in disc_ideal.values()))
        norm_real = math.sqrt(sum(v ** 2 for v in disc_real.values()))
        
        if norm_ideal == 0 or norm_real == 0:
            return 0.5
        
        similarity = dot_product / (norm_ideal * norm_real)
        return max(0, min(1, similarity))
    
    def _score_age(self, employee):
        """Оценка возраста (0-1)"""
        if not employee.age:
            return 0.5
        
        age_min = self.ideal.age_min or 18
        age_max = self.ideal.age_max or 65
        
        if age_min <= employee.age <= age_max:
            return 1.0
        elif employee.age < age_min:
            return max(0, 1 - (age_min - employee.age) / age_min)
        else:
            return max(0, 1 - (employee.age - age_max) / 50)
    
    def _score_generation(self, employee):
        """Оценка поколения (0-1)"""
        if not employee.generation or not self.ideal.generation_preferred:
            return 0.5
        
        return 1.0 if employee.generation == self.ideal.generation_preferred else 0.0
    
    def _score_gerchikov(self, employee):
        """Оценка мотивации по Герчикову (0-1)"""
        if not employee.gerchikov_type or not self.ideal.gerchikov_preferred:
            return 0.5
        
        # Словарь совместимости мотивационных типов
        compatibility = {
            ('instrumental', 'instrumental'): 1.0,
            ('instrumental', 'professional'): 0.7,
            ('instrumental', 'patriotic'): 0.5,
            ('instrumental', 'administrative'): 0.6,
            ('instrumental', 'master'): 0.8,
            
            ('professional', 'professional'): 1.0,
            ('professional', 'instrumental'): 0.8,
            ('professional', 'patriotic'): 0.6,
            ('professional', 'master'): 0.7,
            
            ('patriotic', 'patriotic'): 1.0,
            ('patriotic', 'administrative'): 0.8,
            ('patriotic', 'professional'): 0.6,
            
            ('administrative', 'administrative'): 1.0,
            ('administrative', 'patriotic'): 0.7,
            
            ('master', 'master'): 1.0,
            ('master', 'instrumental'): 0.9,
        }
        
        key = (employee.gerchikov_type, self.ideal.gerchikov_preferred)
        return compatibility.get(key, 0.4)
    
    def _score_role_functions(self, employee):
        """
        Оценка соответствия функций роли.
        """
        ideal_functions = set(self.ideal.role_functions or [])
        
        if not ideal_functions or not employee.disc_scores:
            return self._score_disc(employee)
        
        disc = employee.disc_scores or {'D': 25, 'I': 25, 'S': 25, 'C': 25}
        max_disc = max(disc, key=disc.get)
        
        disc_to_functions = {
            'D': {'sells', 'leads', 'negotiates'},
            'I': {'sells', 'negotiates', 'recruits'},
            'S': {'supports', 'processes'},
            'C': {'analyzes', 'processes', 'creates'},
        }
        
        employee_functions = disc_to_functions.get(max_disc, set())
        
        if not employee_functions:
            return 0.5
        
        # Jaccard similarity (пересечение / объединение)
        intersection = len(ideal_functions & employee_functions)
        union = len(ideal_functions | employee_functions)
        
        return intersection / union if union > 0 else 0.0


def get_recommendations(ideal_profile, limit=10):
    """
    Возвращает топ-N сотрудников, отсортированных по соответствию
    """
    scorer = EmployeeScorer(ideal_profile)
    candidates = Employee.objects.filter(is_active_candidate=True)
    
    results = []
    for employee in candidates:
        score, breakdown = scorer.calculate_match_score(employee)
        results.append({
            'employee': employee,
            'score': score,
            'breakdown': breakdown,
        })
    
    # Сортировка по убыванию балла
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:limit]