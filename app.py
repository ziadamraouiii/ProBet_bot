"""
ProBet - Football Prediction App (Real API Version)
Fixed: Time Leakage, Real Data, TimeSeriesSplit
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
import logging
import warnings
import time

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# PART 1: REAL DATA FETCHER (API-Football)
# ═══════════════════════════════════════════════════════

@dataclass
class MatchData:
    match_id: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    date: datetime
    league: str
    season: str
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None
    home_corners: Optional[int] = None
    away_corners: Optional[int] = None
    home_fouls: Optional[int] = None
    away_fouls: Optional[int] = None
    home_yellow_cards: Optional[int] = None
    away_yellow_cards: Optional[int] = None
    home_red_cards: Optional[int] = None
    away_red_cards: Optional[int] = None

class RealFootballDataFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

    @st.cache_data(ttl=3600, show_spinner=False)
    def fetch_leagues(_self):
        """جلب الدوريات المتاحة"""
        url = f"{_self.base_url}/leagues"
        try:
            resp = requests.get(url, headers=_self.headers)
            if resp.status_code == 200:
                data = resp.json()
                leagues = {}
                for item in data['response']:
                    league = item['league']
                    if league['type'] == 'League':
                        leagues[league['name']] = league['id']
                return leagues
            return {}
        except Exception as e:
            logger.error(f"API League Error: {e}")
            return {}

    @st.cache_data(ttl=7200, show_spinner=False)
    def fetch_historical_data(_self, league_id: int, season: str, limit: int = 1500):
        """جلب المباريات التاريخية مع الإحصائيات"""
        fixtures_url = f"{_self.base_url}/fixtures"
        params = {"league": league_id, "season": season, "status": "FT"}
        
        try:
            resp = requests.get(fixtures_url, headers=_self.headers, params=params)
            if resp.status_code != 200:
                return pd.DataFrame()
            
            fixtures = resp.json().get('response', [])
            if not fixtures:
                return pd.DataFrame()
            
            matches = []
            total = len(fixtures)
            # تحديد حد أقصى للتجربة
            if total > limit:
                fixtures = fixtures[:limit]
            
            progress_bar = st.progress(0, text="جلب الإحصائيات التفصيلية...")
            
            for idx, f in enumerate(fixtures):
                f_data = f['fixture']
                teams = f['teams']
                goals = f['goals']
                
                # جلب الإحصائيات لكل مباراة
                stat_url = f"{_self.base_url}/fixtures/statistics"
                stat_resp = requests.get(stat_url, headers=_self.headers, params={"fixture": f_data['id']})
                stats = {}
                if stat_resp.status_code == 200:
                    stat_data = stat_resp.json().get('response', [])
                    if stat_data and isinstance(stat_data, list) and len(stat_data) > 0:
                        for team_stat in stat_data[0]:
                            team_name = team_stat['team']['name']
                            for stat_item in team_stat['statistics']:
                                key = stat_item['type'].lower().replace(' ', '_')
                                val = stat_item['value']
                                if val is None:
                                    val = 0
                                elif isinstance(val, str) and '%' in val:
                                    val = float(val.replace('%', ''))
                                stats[f"{team_name}_{key}"] = val
                
                home_name = teams['home']['name']
                away_name = teams['away']['name']
                
                # استخراج القيم (مع fallback)
                def get_stat(prefix, key, default=0):
                    val = stats.get(f"{prefix}_{key}", default)
                    if isinstance(val, str):
                        try: return float(val)
                        except: return default
                    return val if val is not None else default
                
                # API لا يوفر xG مجاناً، نستخدم معادلة تقديرية عادلة (0.3 * التسديد على المرمى)
                home_xg = get_stat(home_name, 'shots_on_goal', 0) * 0.3
                away_xg = get_stat(away_name, 'shots_on_goal', 0) * 0.3
                
                match = {
                    'match_id': f_data['id'],
                    'home_team': home_name,
                    'away_team': away_name,
                    'home_goals': goals['home'] or 0,
                    'away_goals': goals['away'] or 0,
                    'date': datetime.strptime(f_data['date'][:10], '%Y-%m-%d'),
                    'league': f_data['league']['name'],
                    'season': season,
                    'home_xg': home_xg,
                    'away_xg': away_xg,
                    'home_possession': get_stat(home_name, 'possession', 50),
                    'away_possession': get_stat(away_name, 'possession', 50),
                    'home_shots': get_stat(home_name, 'total_shots', 0),
                    'away_shots': get_stat(away_name, 'total_shots', 0),
                    'home_shots_on_target': get_stat(home_name, 'shots_on_goal', 0),
                    'away_shots_on_target': get_stat(away_name, 'shots_on_goal', 0),
                    'home_corners': get_stat(home_name, 'corner_kicks', 0),
                    'away_corners': get_stat(away_name, 'corner_kicks', 0),
                    'home_fouls': get_stat(home_name, 'fouls', 0),
                    'away_fouls': get_stat(away_name, 'fouls', 0),
                    'home_yellow_cards': get_stat(home_name, 'yellow_cards', 0),
                    'away_yellow_cards': get_stat(away_name, 'yellow_cards', 0),
                    'home_red_cards': get_stat(home_name, 'red_cards', 0),
                    'away_red_cards': get_stat(away_name, 'red_cards', 0),
                }
                matches.append(match)
                progress_bar.progress((idx + 1) / total, text=f"تم جلب {idx+1}/{total}")
            
            progress_bar.empty()
            return pd.DataFrame(matches)
        except Exception as e:
            logger.error(f"Fetch Error: {e}")
            st.error(f"خطأ في جلب البيانات: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=1800, show_spinner=False)
    def fetch_upcoming_matches(_self, league_id: int, season: str):
        """جلب المباريات القادمة للتنبؤ"""
        url = f"{_self.base_url}/fixtures"
        params = {"league": league_id, "season": season, "status": "NS"}
        try:
            resp = requests.get(url, headers=_self.headers, params=params)
            if resp.status_code == 200:
                data = resp.json().get('response', [])
                matches = []
                for f in data:
                    f_data = f['fixture']
                    teams = f['teams']
                    matches.append({
                        'match_id': f_data['id'],
                        'home_team': teams['home']['name'],
                        'away_team': teams['away']['name'],
                        'date': datetime.strptime(f_data['date'][:10], '%Y-%m-%d'),
                        'league': f_data['league']['name'],
                        'season': season
                    })
                return pd.DataFrame(matches)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Upcoming Error: {e}")
            return pd.DataFrame()

# ═══════════════════════════════════════════════════════
# PART 2: ADVANCED ANALYZER (FIXED TIME LEAKAGE)
# ═══════════════════════════════════════════════════════

class AdvancedFootballAnalyzer:
    def __init__(self, matches_df: pd.DataFrame):
        self.df = matches_df.copy()
        if not self.df.empty:
            self.df['date'] = pd.to_datetime(self.df['date'])
        self._cache = {}  # لتسريع الحساب المتكرر

    def _get_team_stats(self, team: str, cutoff_date: datetime) -> Dict:
        """حساب إحصائيات الفريق فقط من المباريات السابقة للتاريخ المحدد"""
        cache_key = f"{team}_{cutoff_date.strftime('%Y%m%d')}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # فلترة المباريات السابقة
        team_matches = self.df[
            ((self.df['home_team'] == team) | (self.df['away_team'] == team)) &
            (self.df['date'] < cutoff_date)
        ]
        
        if len(team_matches) == 0:
            stats = {
                'matches': 0, 'goals_scored': 0, 'goals_conceded': 0,
                'xg_scored': 0.0, 'xg_conceded': 0.0,
                'wins': 0, 'draws': 0, 'losses': 0,
                'home_wins': 0, 'home_draws': 0, 'home_losses': 0,
                'away_wins': 0, 'away_draws': 0, 'away_losses': 0,
                'form': [], 'yellow_avg': 0, 'red_avg': 0,
                'shots_on_target': 0, 'goals_against_avg': 1.5
            }
        else:
            goals_scored = goals_conceded = 0
            xg_scored = xg_conceded = 0.0
            wins = draws = losses = 0
            h_wins = h_draws = h_losses = 0
            a_wins = a_draws = a_losses = 0
            yellows = reds = 0
            shots_on_target = 0
            goals_against = []

            for _, row in team_matches.iterrows():
                if row['home_team'] == team:
                    goals_scored += row['home_goals']
                    goals_conceded += row['away_goals']
                    xg_scored += row.get('home_xg', 0) or 0
                    xg_conceded += row.get('away_xg', 0) or 0
                    shots_on_target += row.get('home_shots_on_target', 0) or 0
                    goals_against.append(row['away_goals'])
                    if row['home_goals'] > row['away_goals']:
                        wins += 1; h_wins += 1
                    elif row['home_goals'] == row['away_goals']:
                        draws += 1; h_draws += 1
                    else:
                        losses += 1; h_losses += 1
                    yellows += row.get('home_yellow_cards', 0) or 0
                    reds += row.get('home_red_cards', 0) or 0
                else:
                    goals_scored += row['away_goals']
                    goals_conceded += row['home_goals']
                    xg_scored += row.get('away_xg', 0) or 0
                    xg_conceded += row.get('home_xg', 0) or 0
                    shots_on_target += row.get('away_shots_on_target', 0) or 0
                    goals_against.append(row['home_goals'])
                    if row['away_goals'] > row['home_goals']:
                        wins += 1; a_wins += 1
                    elif row['away_goals'] == row['home_goals']:
                        draws += 1; a_draws += 1
                    else:
                        losses += 1; a_losses += 1
                    yellows += row.get('away_yellow_cards', 0) or 0
                    reds += row.get('away_red_cards', 0) or 0

            # الشكل (آخر 5)
            recent = team_matches.sort_values('date').tail(5)
            form = []
            for _, row in recent.iterrows():
                if row['home_team'] == team:
                    form.append('W' if row['home_goals'] > row['away_goals'] else 'D' if row['home_goals'] == row['away_goals'] else 'L')
                else:
                    form.append('W' if row['away_goals'] > row['home_goals'] else 'D' if row['away_goals'] == row['home_goals'] else 'L')
            
            n = len(team_matches)
            stats = {
                'matches': n,
                'goals_scored': goals_scored,
                'goals_conceded': goals_conceded,
                'xg_scored': xg_scored,
                'xg_conceded': xg_conceded,
                'wins': wins, 'draws': draws, 'losses': losses,
                'home_wins': h_wins, 'home_draws': h_draws, 'home_losses': h_losses,
                'away_wins': a_wins, 'away_draws': a_draws, 'away_losses': a_losses,
                'form': form,
                'yellow_avg': yellows / n if n > 0 else 0,
                'red_avg': reds / n if n > 0 else 0,
                'shots_on_target': shots_on_target,
                'goals_against_avg': np.mean(goals_against) if goals_against else 1.5
            }
        
        self._cache[cache_key] = stats
        return stats

    def get_all_factors(self, home_team: str, away_team: str, match_date: datetime) -> Dict:
        """استخراج العوامل الثمانية بناءً على التاريخ"""
        home_stats = self._get_team_stats(home_team, match_date)
        away_stats = self._get_team_stats(away_team, match_date)
        
        # حساب العوامل
        def form_score(stats):
            if not stats['form']:
                return 0.5
            pts = sum(3 if r == 'W' else 1 if r == 'D' else 0 for r in stats['form'])
            return pts / (len(stats['form']) * 3)
        
        def offensive(stats):
            if stats['matches'] == 0: return 1.0
            avg_g = stats['goals_scored'] / stats['matches']
            avg_xg = stats['xg_scored'] / stats['matches']
            return max(0.1, avg_g * 0.4 + avg_xg * 0.6)
        
        def defensive(stats):
            if stats['matches'] == 0: return 1.0
            avg_con = stats['goals_conceded'] / stats['matches']
            avg_xgc = stats['xg_conceded'] / stats['matches']
            combined = avg_con * 0.4 + avg_xgc * 0.6
            return max(0.1, 1 / (1 + combined))
        
        def home_advantage(stats):
            total = stats['home_wins'] + stats['home_draws'] + stats['home_losses']
            if total == 0: return 0.5
            return (stats['home_wins'] * 3 + stats['home_draws']) / (total * 3)
        
        def away_advantage(stats):
            total = stats['away_wins'] + stats['away_draws'] + stats['away_losses']
            if total == 0: return 0.5
            return (stats['away_wins'] * 3 + stats['away_draws']) / (total * 3)
        
        # المواجهات المباشرة (بدون تسرب زمني)
        h2h = self.df[
            ((self.df['home_team'] == home_team) & (self.df['away_team'] == away_team)) |
            ((self.df['home_team'] == away_team) & (self.df['away_team'] == home_team))
        ]
        h2h = h2h[h2h['date'] < match_date].sort_values('date').tail(10)
        h_w = a_w = d = 0
        for _, row in h2h.iterrows():
            if row['home_team'] == home_team:
                if row['home_goals'] > row['away_goals']: h_w += 1
                elif row['home_goals'] < row['away_goals']: a_w += 1
                else: d += 1
            else:
                if row['away_goals'] > row['home_goals']: h_w += 1
                elif row['away_goals'] < row['home_goals']: a_w += 1
                else: d += 1
        total_h2h = h_w + a_w + d
        if total_h2h == 0:
            h2h_vals = {'home': 0.5, 'away': 0.5, 'draw': 0.33}
        else:
            h2h_vals = {'home': h_w/total_h2h, 'away': a_w/total_h2h, 'draw': d/total_h2h}
        
        def discipline(stats):
            return max(0.1, min(1.0, 1 - (stats['yellow_avg'] * 0.05 + stats['red_avg'] * 0.3)))
        
        def efficiency(stats):
            if stats['shots_on_target'] == 0: return 0.3
            return min(1.0, (stats['goals_scored'] / stats['shots_on_target']) / 0.3)
        
        def momentum(stats):
            if len(stats['form']) < 5: return 0.5
            results = [1 if f == 'W' else 0 if f == 'L' else 0.5 for f in stats['form']]
            if len(results) < 2: return 0.5
            return np.mean(results)  # تبسيط بدلاً من الانحدار الخطي

        return {
            'home_form': form_score(home_stats),
            'away_form': form_score(away_stats),
            'home_offense': offensive(home_stats),
            'away_offense': offensive(away_stats),
            'home_defense': defensive(home_stats),
            'away_defense': defensive(away_stats),
            'home_advantage': home_advantage(home_stats),
            'away_advantage': away_advantage(away_stats),
            'h2h_home': h2h_vals['home'],
            'h2h_draw': h2h_vals['draw'],
            'home_discipline': discipline(home_stats),
            'away_discipline': discipline(away_stats),
            'home_efficiency': efficiency(home_stats),
            'away_efficiency': efficiency(away_stats),
            'home_momentum': momentum(home_stats),
            'away_momentum': momentum(away_stats),
        }

# ═══════════════════════════════════════════════════════
# PART 3: PREDICTION MODELS (FIXED TIME SPLIT)
# ═══════════════════════════════════════════════════════

class FootballPredictionModels:
    def __init__(self):
        self.rf_model = None
        self.xgb_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.analyzer = None

    def prepare_features(self, df: pd.DataFrame, analyzer, match_date=None) -> pd.DataFrame:
        features_list = []
        for idx, row in df.iterrows():
            date = match_date if match_date else row['date']
            factors = analyzer.get_all_factors(row['home_team'], row['away_team'], date)
            h_stats = analyzer._get_team_stats(row['home_team'], date)
            a_stats = analyzer._get_team_stats(row['away_team'], date)
            
            feature_vector = {
                'form_diff': factors['home_form'] - factors['away_form'],
                'offense_diff': factors['home_offense'] - factors['away_offense'],
                'defense_diff': factors['home_defense'] - factors['away_defense'],
                'home_ground_advantage': factors['home_advantage'] - factors['away_advantage'],
                'h2h_home_bias': factors['h2h_home'] - factors['h2h_away'],
                'h2h_draw_tendency': factors['h2h_draw'],
                'discipline_diff': factors['home_discipline'] - factors['away_discipline'],
                'efficiency_diff': factors['home_efficiency'] - factors['away_efficiency'],
                'momentum_diff': factors['home_momentum'] - factors['away_momentum'],
                'home_goals_avg': (h_stats['goals_scored'] / max(1, h_stats['matches'])),
                'away_goals_avg': (a_stats['goals_scored'] / max(1, a_stats['matches'])),
                'home_conceded_avg': (h_stats['goals_conceded'] / max(1, h_stats['matches'])),
                'away_conceded_avg': (a_stats['goals_conceded'] / max(1, a_stats['matches'])),
            }
            features_list.append(feature_vector)
        
        features_df = pd.DataFrame(features_list)
        # تعبئة القيم المفقودة
        features_df = features_df.fillna(0)
        self.feature_names = features_df.columns.tolist()
        return features_df

    def create_target(self, df: pd.DataFrame) -> np.ndarray:
        targets = []
        for _, row in df.iterrows():
            if row['home_goals'] > row['away_goals']: targets.append(2)
            elif row['home_goals'] == row['away_goals']: targets.append(1)
            else: targets.append(0)
        return np.array(targets)

    def train(self, X: pd.DataFrame, y: np.ndarray, dates: pd.Series):
        """تدريب مع TimeSeriesSplit لمنع التسرب"""
        # ترتيب حسب التاريخ
        sorted_idx = np.argsort(dates)
        X = X.iloc[sorted_idx].reset_index(drop=True)
        y = y[sorted_idx]
        
        # استخدام TimeSeriesSplit
        tscv = TimeSeriesSplit(n_splits=3)
        rf_scores = []
        xgb_scores = []
        lr_scores = []
        
        # تدريب أخير split للتقييم النهائي
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # StandardScaler
            self.scaler.fit(X_train)
            X_train_scaled = self.scaler.transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Random Forest
            rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
            rf.fit(X_train, y_train)
            rf_scores.append(accuracy_score(y_test, rf.predict(X_test)))
            
            # XGBoost (fallback)
            try:
                import xgboost as xgb
                xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=5, random_state=42, eval_metric='mlogloss')
                xgb_model.fit(X_train, y_train)
                xgb_scores.append(accuracy_score(y_test, xgb_model.predict(X_test)))
            except:
                from sklearn.ensemble import GradientBoostingClassifier
                xgb_model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
                xgb_model.fit(X_train, y_train)
                xgb_scores.append(accuracy_score(y_test, xgb_model.predict(X_test)))
            
            # LR
            lr = LogisticRegression(max_iter=1000, random_state=42, multi_class='multinomial')
            lr.fit(X_train_scaled, y_train)
            lr_scores.append(accuracy_score(y_test, lr.predict(X_test_scaled)))
            
            # حفظ آخر نموذج مدرب
            self.rf_model = rf
            self.xgb_model = xgb_model
            self.lr_model = lr
        
        # التدريب النهائي على كامل البيانات (باستثناء آخر 20% للاختبار)
        train_size = int(len(X) * 0.8)
        X_train_final, X_test_final = X.iloc[:train_size], X.iloc[train_size:]
        y_train_final, y_test_final = y[:train_size], y[train_size:]
        
        self.scaler.fit(X_train_final)
        X_train_scaled = self.scaler.transform(X_train_final)
        X_test_scaled = self.scaler.transform(X_test_final)
        
        self.rf_model.fit(X_train_final, y_train_final)
        self.xgb_model.fit(X_train_final, y_train_final)
        self.lr_model.fit(X_train_scaled, y_train_final)
        
        final_acc = accuracy_score(y_test_final, self.rf_model.predict(X_test_final))
        self.is_trained = True
        
        return {
            'rf_avg': np.mean(rf_scores),
            'xgb_avg': np.mean(xgb_scores),
            'lr_avg': np.mean(lr_scores),
            'final_accuracy': final_acc,
            'samples': len(X)
        }

    def predict(self, X: pd.DataFrame) -> Dict:
        if not self.is_trained:
            raise ValueError("Models not trained!")
        X_scaled = self.scaler.transform(X)
        
        rf_probs = self.rf_model.predict_proba(X)[0]
        xgb_probs = self.xgb_model.predict_proba(X)[0]
        lr_probs = self.lr_model.predict_proba(X_scaled)[0]
        
        # Ensemble
        ensemble_probs = rf_probs * 0.30 + xgb_probs * 0.45 + lr_probs * 0.25
        labels = ['Away Win', 'Draw', 'Home Win']
        classes = ['away_win', 'draw', 'home_win']
        
        return {
            'ensemble_prediction': labels[np.argmax(ensemble_probs)],
            'ensemble_class': classes[np.argmax(ensemble_probs)],
            'probabilities': {
                'away_win': round(ensemble_probs[0] * 100, 1),
                'draw': round(ensemble_probs[1] * 100, 1),
                'home_win': round(ensemble_probs[2] * 100, 1)
            },
            'confidence': round(max(ensemble_probs) * 100, 1)
        }

# ═══════════════════════════════════════════════════════
# PART 4: STREAMLIT UI
# ═══════════════════════════════════════════════════════

st.set_page_config(page_title="ProBet Pro - Real API", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.8rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #1e3a8a, #3b82f6, #1e3a8a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .metric-card { background: #1e293b; border-radius: 15px; padding: 1.5rem; border: 1px solid #334155; text-align: center; }
    .metric-value { font-size: 2.5rem; font-weight: 900; color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚽ ProBet Pro (Real API)</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🔑 الإعدادات")
    api_key = st.text_input("مفتاح API-Football", value="800b354d6fa7590c158b6078e1b72381", type="password")
    st.markdown("---")
    
    if api_key:
        fetcher = RealFootballDataFetcher(api_key)
        leagues = fetcher.fetch_leagues()
        
        if leagues:
            league_names = list(leagues.keys())
            selected_league_name = st.selectbox("🏆 اختر الدوري", league_names, index=0)
            league_id = leagues[selected_league_name]
            
            seasons = ["2024", "2023", "2022"]
            selected_season = st.selectbox("📅 الموسم", seasons, index=0)
            
            if st.button("🚀 تحميل البيانات التاريخية", use_container_width=True):
                with st.spinner("جاري تحميل المباريات..."):
                    df = fetcher.fetch_historical_data(league_id, selected_season, limit=800)
                    if not df.empty:
                        st.session_state.df = df
                        st.session_state.analyzer = AdvancedFootballAnalyzer(df)
                        st.session_state.models = FootballPredictionModels()
                        st.session_state.models.analyzer = st.session_state.analyzer
                        
                        # تجهيز التدريب
                        X = st.session_state.models.prepare_features(df, st.session_state.analyzer)
                        y = st.session_state.models.create_target(df)
                        results = st.session_state.models.train(X, y, df['date'])
                        st.session_state.training_results = results
                        st.session_state.data_loaded = True
                        st.success(f"✅ تم تحميل {len(df)} مباراة! الدقة: {results['final_accuracy']:.1%}")
                    else:
                        st.error("لا توجد بيانات أو خطأ في المفتاح")
            
            st.markdown("---")
            if st.button("📅 جلب المباريات القادمة", use_container_width=True):
                upcoming = fetcher.fetch_upcoming_matches(league_id, selected_season)
                if not upcoming.empty:
                    st.session_state.upcoming = upcoming
                    st.success(f"✅ تم جلب {len(upcoming)} مباراة قادمة")
                else:
                    st.warning("لا توجد مباريات قادمة حالياً")
        else:
            st.error("فشل الاتصال بالـ API. تأكد من المفتاح.")

# Main Tabs
if 'data_loaded' in st.session_state and st.session_state.data_loaded:
    tabs = st.tabs(["🔮 التنبؤ", "📊 التحليلات", "🤖 الأداء"])
    
    with tabs[0]:
        st.markdown("## 🔮 تنبؤ المباريات القادمة")
        if 'upcoming' in st.session_state and not st.session_state.upcoming.empty:
            upcoming = st.session_state.upcoming
            match_options = [f"{row['home_team']} vs {row['away_team']} ({row['date'].date()})" for _, row in upcoming.iterrows()]
            selected_match = st.selectbox("اختر المباراة", match_options)
            
            if st.button("🔮 تنبأ", type="primary"):
                idx = match_options.index(selected_match)
                row = upcoming.iloc[idx]
                
                with st.spinner("تحليل 8 عوامل..."):
                    factors = st.session_state.analyzer.get_all_factors(row['home_team'], row['away_team'], datetime.now())
                    temp_df = pd.DataFrame([{
                        'home_team': row['home_team'],
                        'away_team': row['away_team'],
                        'date': datetime.now()
                    }])
                    X_pred = st.session_state.models.prepare_features(temp_df, st.session_state.analyzer, datetime.now())
                    pred = st.session_state.models.predict(X_pred)
                    
                    st.markdown("---")
                    c1, c2, c3 = st.columns([2,1,2])
                    with c1:
                        st.markdown(f"<h3 style='text-align:center;color:#3b82f6;'>{row['home_team']}</h3>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("<h1 style='text-align:center;color:#f59e0b;'>VS</h1>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"<h3 style='text-align:center;color:#ef4444;'>{row['away_team']}</h3>", unsafe_allow_html=True)
                    
                    probs = pred['probabilities']
                    cols = st.columns(3)
                    cols[0].metric(f"فوز {row['away_team']}", f"{probs['away_win']}%")
                    cols[1].metric("تعادل", f"{probs['draw']}%")
                    cols[2].metric(f"فوز {row['home_team']}", f"{probs['home_win']}%")
                    
                    st.success(f"🏆 التنبؤ النهائي: **{pred['ensemble_prediction']}** (ثقة {pred['confidence']}%)")
                    
                    # عرض العوامل
                    st.markdown("### 📈 العوامل التحليلية")
                    fact_df = pd.DataFrame({
                        'العامل': ['Form', 'Offense', 'Defense', 'Home Adv.', 'H2H', 'Discipline', 'Efficiency', 'Momentum'],
                        row['home_team']: [factors['home_form'], factors['home_offense'], factors['home_defense'], factors['home_advantage'], factors['h2h_home'], factors['home_discipline'], factors['home_efficiency'], factors['home_momentum']],
                        row['away_team']: [factors['away_form'], factors['away_offense'], factors['away_defense'], factors['away_advantage'], factors['h2h_away'], factors['away_discipline'], factors['away_efficiency'], factors['away_momentum']]
                    })
                    st.dataframe(fact_df.style.format("{:.2f}"), use_container_width=True)
        else:
            st.info("اضغط على 'جلب المباريات القادمة' في القائمة الجانبية أولاً.")
    
    with tabs[1]:
        df = st.session_state.df
        st.markdown("## 📊 إحصائيات الدوري")
        col1, col2, col3 = st.columns(3)
        col1.metric("المباريات", len(df))
        avg_goals = (df['home_goals'].sum() + df['away_goals'].sum()) / len(df)
        col2.metric("متوسط الأهداف", f"{avg_goals:.2f}")
        home_win_rate = (df['home_goals'] > df['away_goals']).sum() / len(df) * 100
        col3.metric("نسبة فوز الأرض", f"{home_win_rate:.1f}%")
        
        fig = px.histogram(df['home_goals'] + df['away_goals'], nbins=10, title="توزيع الأهداف")
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:
        res = st.session_state.training_results
        st.markdown("## 🤖 أداء النماذج (TimeSeriesSplit)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Random Forest", f"{res['rf_avg']:.1%}")
        c2.metric("XGBoost", f"{res['xgb_avg']:.1%}")
        c3.metric("Logistic Reg.", f"{res['lr_avg']:.1%}")
        st.metric("الدقة النهائية (آخر 20%)", f"{res['final_accuracy']:.1%}")
        st.caption("تم التقييم باستخدام TimeSeriesSplit لمنع التسرب الزمني (التنبؤ بالمستقبل).")

else:
    st.info("⏳ يرجى تحميل البيانات من القائمة الجانبية أولاً باستخدام مفتاح API الصحيح.")
