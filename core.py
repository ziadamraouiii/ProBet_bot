import math

def calculate_poisson(home_exp, away_exp):
    def poisson(k, lam):
        return (lam**k * math.exp(-lam)) / math.factorial(k)
    
    # مصفوفة احتمالات النتائج (0-0 إلى 5-5 كافية دقيقة)
    matrix = [[0 for _ in range(6)] for _ in range(6)]
    home_win, draw, away_win = 0, 0, 0
    btts_prob = 0
    over_2_5 = 0
    
    for i in range(6):
        for j in range(6):
            prob = poisson(i, home_exp) * poisson(j, away_exp)
            matrix[i][j] = prob
            
            # النتائج الأساسية
            if i > j: home_win += prob
            elif j > i: away_win += prob
            else: draw += prob
            
            # الاحتمالات المتقدمة
            if i > 0 and j > 0: btts_prob += prob
            if (i + j) > 2.5: over_2_5 += prob
            
    return {
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win,
        "btts": btts_prob,
        "over_2_5": over_2_5,
        "over_1_5": 1 - (matrix[0][0] + matrix[1][0] + matrix[0][1]),
        "double_chance_home": home_win + draw,
        "double_chance_away": away_win + draw
    }

def get_moving_average_stats(matches_data):
    weights = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.35, 0.3, 0.25]
    w_scored, w_conceded, total_weight = 0, 0, 0
    
    for idx, (sc, cn) in enumerate(matches_data):
        weight = weights[idx] if idx < len(weights) else 0.2
        w_scored += (sc * weight)
        w_conceded += (cn * weight)
        total_weight += weight
        
    return round(w_scored / total_weight, 2), round(w_conceded / total_weight, 2)
