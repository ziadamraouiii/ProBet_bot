import math

def calculate_poisson(home_exp, away_exp):
    def poisson(k, lam):
        return (lam**k * math.exp(-lam)) / math.factorial(k)
    
    home_win, draw, away_win = 0, 0, 0
    # حساب احتمالات النتائج من 0-0 إلى 7-7
    for i in range(8):
        for j in range(8):
            prob = poisson(i, home_exp) * poisson(j, away_exp)
            if i > j: home_win += prob
            elif j > i: away_win += prob
            else: draw += prob
    return home_win, draw, away_win

def get_moving_average_stats(matches_data):
    # تطبيق "الوزن الذكي" (أهمية أكبر للمباريات الحديثة)
    total_weight = 0
    w_scored = 0
    w_conceded = 0
    weights = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.35, 0.3, 0.25]
    
    for idx, (sc, cn) in enumerate(matches_data):
        weight = weights[idx] if idx < len(weights) else 0.2
        w_scored += (sc * weight)
        w_conceded += (cn * weight)
        total_weight += weight
        
    return round(w_scored / total_weight, 2), round(w_conceded / total_weight, 2)
