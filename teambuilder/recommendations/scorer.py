import math
from profiles.models import Employee
 
 
MOTIV_FUNCTION_FIT = {
    'instrumental': {
        'sells': 0.95, 'negotiates': 0.90, 'leads': 0.70,
        'creates': 0.50, 'analyzes': 0.45, 'supports': 0.30,
        'processes': 0.25, 'recruits': 0.35,
    },
    'professional': {
        'creates': 0.95, 'analyzes': 0.90, 'leads': 0.60,
        'sells': 0.50, 'supports': 0.60, 'negotiates': 0.55,
        'processes': 0.55, 'recruits': 0.55,
    },
    'patriotic': {
        'recruits': 0.95, 'supports': 0.90, 'leads': 0.75,
        'processes': 0.70, 'analyzes': 0.55, 'sells': 0.45,
        'creates': 0.50, 'negotiates': 0.50,
    },
    'administrative': {
        'leads': 0.90, 'processes': 0.85, 'recruits': 0.70,
        'analyzes': 0.60, 'negotiates': 0.65, 'supports': 0.50,
        'sells': 0.40, 'creates': 0.35,
    },
    'master': {
        'leads': 0.95, 'creates': 0.85, 'analyzes': 0.80,
        'negotiates': 0.70, 'sells': 0.60, 'recruits': 0.45,
        'supports': 0.30, 'processes': 0.25,
    },
    'mixed': {
        'sells': 0.60, 'analyzes': 0.60, 'supports': 0.60,
        'leads': 0.65, 'creates': 0.60, 'processes': 0.55,
        'recruits': 0.60, 'negotiates': 0.60,
    },
}
 
GERCHIKOV_COMPAT = {
    ('instrumental', 'instrumental'): 1.00,
    ('instrumental', 'master'):       0.85,
    ('instrumental', 'professional'): 0.65,
    ('instrumental', 'administrative'): 0.55,
    ('instrumental', 'patriotic'):    0.40,
    ('instrumental', 'mixed'):        0.60,
 
    ('professional', 'professional'): 1.00,
    ('professional', 'master'):       0.75,
    ('professional', 'instrumental'): 0.70,
    ('professional', 'patriotic'):    0.55,
    ('professional', 'administrative'): 0.45,
    ('professional', 'mixed'):        0.60,
 
    ('patriotic', 'patriotic'):       1.00,
    ('patriotic', 'administrative'):  0.75,
    ('patriotic', 'professional'):    0.55,
    ('patriotic', 'mixed'):           0.60,
    ('patriotic', 'instrumental'):    0.35,
    ('patriotic', 'master'):          0.40,
 
    ('administrative', 'administrative'): 1.00,
    ('administrative', 'patriotic'):  0.75,
    ('administrative', 'professional'): 0.55,
    ('administrative', 'mixed'):      0.60,
    ('administrative', 'instrumental'): 0.45,
    ('administrative', 'master'):     0.50,
 
    ('master', 'master'):             1.00,
    ('master', 'instrumental'):       0.85,
    ('master', 'professional'):       0.70,
    ('master', 'administrative'):     0.50,
    ('master', 'patriotic'):          0.40,
    ('master', 'mixed'):              0.60,
}
 
GEN_STYLE_FIT = {
    ('Z',     'authoritarian'): 0.15,
    ('Z',     'democratic'):    0.75,
    ('Z',     'coaching'):      0.95,
    ('Z',     'delegating'):    0.60,
 
    ('Y',     'authoritarian'): 0.35,
    ('Y',     'democratic'):    0.90,
    ('Y',     'coaching'):      0.85,
    ('Y',     'delegating'):    0.75,
 
    ('X',     'authoritarian'): 0.65,
    ('X',     'democratic'):    0.72,
    ('X',     'coaching'):      0.60,
    ('X',     'delegating'):    0.92,
 
    ('Alpha', 'authoritarian'): 0.10,
    ('Alpha', 'democratic'):    0.70,
    ('Alpha', 'coaching'):      0.95,
    ('Alpha', 'delegating'):    0.55,
 
    ('BB', 'authoritarian'): 0.85,
    ('BB', 'delegating'):    0.80,
    ('BB', 'democratic'):    0.60,
    ('BB', 'coaching'):      0.45,
}
 
WEIGHTS = {
    'disc_fit':       0.35,
    'motivation_fit': 0.30,
    'gerchikov_pref': 0.15,
    'gen_style_fit':  0.12,
    'age_fit':        0.08,
}
 
 
class EmployeeScorer:
 
    def __init__(self, ideal_profile):
        self.ideal = ideal_profile
 
    def score(self, employee: Employee) -> dict:
        axes = {
            'disc_fit':       self._disc_fit(employee),
            'motivation_fit': self._motivation_fit(employee),
            'gerchikov_pref': self._gerchikov_pref(employee),
            'gen_style_fit':  self._gen_style_fit(employee),
            'age_fit':        self._age_fit(employee),
        }
        total = sum(axes[k] * WEIGHTS[k] for k in axes) * 100
        return {
            'employee':    employee,
            'total':       round(total, 1),
            'axes':        {k: round(v, 3) for k, v in axes.items()},
            'explanation': self._explain(axes, employee),
        }
 
    def _disc_fit(self, employee) -> float:
        ideal = self.ideal.disc_preferred or {}
        real  = employee.disc_scores or {}
 
        if not ideal or not real:
            return 0.5
 
        keys = ['D', 'I', 'S', 'C']
 
        # 1. Косинусное сходство — совпадение формы профиля (50% веса)
        dot    = sum(ideal.get(k, 0) * real.get(k, 0) for k in keys)
        n_i    = math.sqrt(sum(ideal.get(k, 0) ** 2 for k in keys)) or 1
        n_r    = math.sqrt(sum(real.get(k,  0) ** 2 for k in keys)) or 1
        cosine = dot / (n_i * n_r)
 
        # 2. Близость абсолютных значений — MAE (50% веса)
        # Если идеал D=80 а сотрудник D=30 — это штрафуется
        # mae в диапазоне 0-100 → нормализуем и инвертируем
        mae       = sum(abs(ideal.get(k, 0) - real.get(k, 0)) for k in keys) / len(keys)
        proximity = max(0.0, 1.0 - mae / 100)
 
        score = cosine * 0.2 + proximity * 0.8
 
        # Небольшой бонус если ведущий тип в предпочитаемых
        preferred   = self.ideal.preferred_personality_types or []
        emp_primary = max(real, key=real.get) if real else None
        bonus = 0.06 if emp_primary and emp_primary in preferred else 0.0
 
        return min(1.0, max(0.0, score + bonus))
 
    def _motivation_fit(self, employee) -> float:
        motiv     = employee.gerchikov_type or 'mixed'
        functions = self.ideal.role_functions or []
        if not functions:
            return 0.5
        motiv_map = MOTIV_FUNCTION_FIT.get(motiv, MOTIV_FUNCTION_FIT['mixed'])
        scores    = [motiv_map.get(fn, 0.35) for fn in functions]
        return round(sum(scores) / len(scores), 3)
 
    def _gerchikov_pref(self, employee) -> float:
        pref  = self.ideal.gerchikov_preferred
        motiv = employee.gerchikov_type
        if not pref or not motiv:
            return 0.5
        return GERCHIKOV_COMPAT.get((motiv, pref), 0.40)
 
    def _gen_style_fit(self, employee) -> float:
        gen   = employee.generation
        style = self.ideal.leadership_style
        if not gen or not style:
            return 0.5
        return GEN_STYLE_FIT.get((gen, style), 0.5)
 
    def _age_fit(self, employee) -> float:
        age     = employee.age
        age_min = self.ideal.age_min or 18
        age_max = self.ideal.age_max or 65
        if not age:
            return 0.5
        if age_min <= age <= age_max:
            return 1.0
        elif age < age_min:
            return max(0.1, 1.0 - (age_min - age) * 0.08)
        else:
            return max(0.1, 1.0 - (age - age_max) * 0.08)
 
    def _explain(self, axes: dict, employee: Employee) -> list:
        lines = []
        real  = employee.disc_scores or {}
        motiv = employee.gerchikov_type or 'mixed'
        gen   = employee.generation or '?'
 
        MOTIV_LABELS = {
            'instrumental':   'ориентирован на результат и доход',
            'professional':   'стремится к профессиональному росту',
            'patriotic':      'ценит причастность и командную атмосферу',
            'administrative': 'ценит статус, стабильность и должность',
            'master':         'предпочитает автономию и ответственность',
            'mixed':          'смешанный тип мотивации',
        }
 
        GEN_LABELS = {
            'X':     'Поколение X — самостоятельные, привыкли к ответственности',
            'Y':     'Поколение Y — ценят смысл, гибкость и развитие',
            'Z':     'Поколение Z — диджитал-нативы, нужен коучинг и честность',
            'BB':    'Бэби-бумеры — опытные, ценят иерархию и стабильность',
            'Alpha': 'Поколение Alpha — гиперперсонализация и технологии',
        }
 
        # DISC
        d = axes['disc_fit']
        emp_primary = max(real, key=real.get) if real else '?'
        if d >= 0.80:
            lines.append(f"DISC-профиль хорошо совпадает с идеалом (ведущий тип: {emp_primary})")
        elif d >= 0.55:
            lines.append(f"DISC частично совпадает — тип {emp_primary}, есть отклонения")
        else:
            lines.append(f"DISC-профиль далёк от идеального (тип {emp_primary})")
 
        # Мотивация
        mf = axes['motivation_fit']
        lines.append(f"💡 Мотивация: {MOTIV_LABELS.get(motiv, motiv)}")
        if mf >= 0.80:
            lines.append(f"Мотивационный профиль хорошо подходит для функций роли")
        elif mf >= 0.55:
            lines.append(f"Мотивация частично совпадает с функциями роли")
        else:
            lines.append(f"Мотивация плохо совпадает с функциями роли — риск выгорания")
 
        # Тип мотивации
        gp = axes['gerchikov_pref']
        if self.ideal.gerchikov_preferred:
            if gp >= 0.85:
                lines.append(f"Тип мотивации совпадает с предпочитаемым")
            elif gp <= 0.45:
                lines.append(f"Тип мотивации отличается от предпочитаемого")
 
        # Поколение
        gs = axes['gen_style_fit']
        lines.append(f"👥 {GEN_LABELS.get(gen, gen)}")
        if gs >= 0.85:
            lines.append(f"Поколение хорошо совместимо с вашим стилем управления")
        elif gs <= 0.35:
            lines.append(f"Поколение {gen} может плохо воспринять ваш стиль управления")
 
        # Возраст
        af      = axes['age_fit']
        age_min = self.ideal.age_min or 18
        age_max = self.ideal.age_max or 65
        if af == 1.0:
            lines.append(f"Возраст ({employee.age}) в диапазоне {age_min}–{age_max}")
        elif af < 0.5:
            lines.append(f"Возраст ({employee.age}) выходит за диапазон {age_min}–{age_max}")
 
        # Зарплата
        sal = (employee.salary_block or {}).get('min', 0)
        if sal:
            lines.append(f"Минимальная зарплата: {sal:,} ₽".replace(',', ' '))
 
        return lines
 
 
def get_recommendations(ideal_profile, limit: int = 10) -> list:
    scorer     = EmployeeScorer(ideal_profile)
    candidates = Employee.objects.filter(is_active_candidate=True)
    results    = [scorer.score(emp) for emp in candidates]
    results.sort(key=lambda x: x['total'], reverse=True)
    return results[:limit]