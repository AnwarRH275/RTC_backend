from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.model import User
from models.tcf_exam_model import TCFExam
from models.tcf_attempt_model import TCFAttempt
from models.tcf_model import TCFSubject
from models.exts import db
from datetime import datetime, timedelta
from sqlalchemy import func, extract

dashboard_ns = Namespace('dashboard', description='Services pour les statistiques du dashboard')

# Modèle pour les statistiques utilisateur
user_stats_model = dashboard_ns.model(
    "UserStats",
    {
        "total_exams": fields.Integer(),
        "average_score": fields.Float(),
        "best_score": fields.Float(),
        "weekly_exams": fields.Integer(),
        "monthly_progress": fields.Integer(),
        "study_streak": fields.Integer(),
        "remaining_credits": fields.Integer()
    }
)

# Modèle pour les statistiques admin
admin_stats_model = dashboard_ns.model(
    "AdminStats",
    {
        "total_users": fields.Integer(),
        "active_users": fields.Integer(),
        "total_exams": fields.Integer(),
        "total_attempts": fields.Integer(),
        "monthly_revenue": fields.Float()
    }
)

# Modèle pour les données de graphique mensuel
monthly_chart_model = dashboard_ns.model(
    "MonthlyChart",
    {
        "month": fields.String(),
        "exams": fields.Integer(),
        "users": fields.Integer()
    }
)

# Modèle pour l'activité récente
recent_activity_model = dashboard_ns.model(
    "RecentActivity",
    {
        "id": fields.Integer(),
        "title": fields.String(),
        "description": fields.String(),
        "date": fields.DateTime(),
        "type": fields.String(),
        "score": fields.String()
    }
)

@dashboard_ns.route("/stats")
class DashboardStatsResource(Resource):
    
    @jwt_required()
    def get(self):
        '''Récupérer les statistiques du dashboard selon le rôle de l\'utilisateur'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
        
        if user.role.lower() == 'client':
            return self._get_client_stats(user)
        elif user.role.lower() in ['admin', 'administrator', 'moderator']:
            return self._get_admin_stats(user)
        else:
            return {'message': 'Rôle non autorisé'}, 403
    
    def _get_client_stats(self, user):
        '''Calculer les statistiques pour un client'''
        # Récupérer tous les examens de l'utilisateur
        exams = TCFExam.query.filter_by(id_user=user.id).all()
        
        # Statistiques de base
        total_exams = len(exams)
        
        # Calcul des scores - gérer les scores textuels comme "Niveau C1"
        scores = []
        for exam in exams:
            if exam.score:
                try:
                    # Essayer de convertir en float d'abord
                    score = float(exam.score)
                    scores.append(score)
                except (ValueError, TypeError):
                    # Si c'est un niveau comme "Niveau C1", assigner une valeur numérique
                    if "C2" in exam.score.upper():
                        scores.append(95)
                    elif "C1" in exam.score.upper():
                        scores.append(85)
                    elif "B2" in exam.score.upper():
                        scores.append(75)
                    elif "B1" in exam.score.upper():
                        scores.append(65)
                    elif "A2" in exam.score.upper():
                        scores.append(55)
                    elif "A1" in exam.score.upper():
                        scores.append(45)
                    else:
                        scores.append(50)  # Score par défaut
        
        average_score = round(sum(scores) / len(scores), 1) if scores else 0
        best_score = max(scores) if scores else 0
        
        # Examens de la semaine dernière
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_exams = len([e for e in exams if e.date_passage and e.date_passage >= week_ago])
        
        # Progression mensuelle (différence avec le mois précédent)
        month_ago = datetime.utcnow() - timedelta(days=30)
        two_months_ago = datetime.utcnow() - timedelta(days=60)
        
        current_month_exams = len([e for e in exams if e.date_passage and e.date_passage >= month_ago])
        previous_month_exams = len([e for e in exams if e.date_passage and two_months_ago <= e.date_passage < month_ago])
        
        monthly_progress = current_month_exams - previous_month_exams
        
        # Série d'étude (jours consécutifs avec au moins un examen)
        study_streak = self._calculate_study_streak(user.id)
        
        # Crédits restants (basé sur le plan d'abonnement)
        remaining_credits = self._calculate_remaining_credits(user)
        
        return {
            'total_exams': total_exams,
            'average_score': average_score,
            'best_score': best_score,
            'weekly_exams': weekly_exams,
            'monthly_progress': monthly_progress,
            'study_streak': study_streak,
            'remaining_credits': remaining_credits
        }
    
    def _get_admin_stats(self, user):
        '''Calculer les statistiques pour un administrateur'''
        # Nombre total d'utilisateurs
        total_users = User.query.count()
        
        # Utilisateurs actifs (avec payment_status = 'active')
        active_users = User.query.filter_by(payment_status='active').count()
        
        # Nombre total d'examens
        total_exams = TCFExam.query.count()
        
        # Nombre total de tentatives
        total_attempts = TCFAttempt.query.count()
        
        # Revenus mensuels (estimation basée sur les plans d'abonnement)
        monthly_revenue = self._calculate_monthly_revenue()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_exams': total_exams,
            'total_attempts': total_attempts,
            'monthly_revenue': monthly_revenue
        }
    
    def _calculate_study_streak(self, user_id):
        '''Calculer la série d\'étude de l\'utilisateur'''
        # Récupérer les dates d'examens triées par date décroissante
        exam_dates = db.session.query(
            func.date(TCFExam.date_passage)
        ).filter(
            TCFExam.id_user == user_id
        ).distinct().order_by(
            func.date(TCFExam.date_passage).desc()
        ).all()
        
        if not exam_dates:
            return 0
        
        streak = 0
        current_date = datetime.utcnow().date()
        
        for (exam_date,) in exam_dates:
            days_diff = (current_date - exam_date).days
            
            if days_diff == streak:
                streak += 1
                current_date = current_date - timedelta(days=1)
            elif days_diff > streak:
                break
        
        return streak
    
    def _calculate_monthly_revenue(self):
        '''Calculer les revenus mensuels estimés'''
        plan_prices = {
            'basic': 29.99,
            'premium': 49.99,
            'pro': 79.99
        }
        
        active_users = User.query.filter_by(payment_status='active').all()
        total_revenue = 0
        
        for user in active_users:
            plan_price = plan_prices.get(user.subscription_plan, 0)
            total_revenue += plan_price
        
        return round(total_revenue, 2)
    
    def _calculate_remaining_credits(self, user):
        '''Calculer les crédits restants de l\'utilisateur'''
        # Crédits basés sur le plan d'abonnement
        plan_credits = {
            'basic': 50,
            'premium': 150,
            'pro': 500,
            'standard': 100,
            'performance': 300
        }
        
        # Crédits de base selon le plan
        base_credits = plan_credits.get(user.subscription_plan, 20)
        
        # Soustraire les examens du mois en cours
        month_ago = datetime.utcnow() - timedelta(days=30)
        monthly_exams = TCFExam.query.filter(
            TCFExam.id_user == user.id,
            TCFExam.date_passage >= month_ago
        ).count()
        
        remaining = max(0, base_credits - monthly_exams)
        
        # Ajouter le solde utilisateur s'il existe
        if user.sold:
            remaining += int(user.sold)
        
        return remaining

@dashboard_ns.route("/chart/monthly")
class DashboardMonthlyChartResource(Resource):
    
    @jwt_required()
    def get(self):
        '''Récupérer les données pour le graphique mensuel'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
        
        # Récupérer les données des 12 derniers mois
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        if user.role == 'Client':
            # Pour les clients, montrer leurs examens par mois
            monthly_data = db.session.query(
                extract('month', TCFExam.date_passage).label('month'),
                extract('year', TCFExam.date_passage).label('year'),
                func.count(TCFExam.id).label('count')
            ).filter(
                TCFExam.id_user == user.id,
                TCFExam.date_passage >= twelve_months_ago
            ).group_by(
                extract('year', TCFExam.date_passage),
                extract('month', TCFExam.date_passage)
            ).order_by(
                extract('year', TCFExam.date_passage),
                extract('month', TCFExam.date_passage)
            ).all()
            
            result = []
            for month, year, count in monthly_data:
                month_name = datetime(int(year), int(month), 1).strftime('%B %Y')
                result.append({
                    'month': month_name,
                    'exams': count,
                    'users': 0  # Non applicable pour les clients
                })
            
        else:
            # Pour les admins, montrer les examens et nouveaux utilisateurs par mois
            exam_data = db.session.query(
                extract('month', TCFExam.date_passage).label('month'),
                extract('year', TCFExam.date_passage).label('year'),
                func.count(TCFExam.id).label('exam_count')
            ).filter(
                TCFExam.date_passage >= twelve_months_ago
            ).group_by(
                extract('year', TCFExam.date_passage),
                extract('month', TCFExam.date_passage)
            ).all()
            
            user_data = db.session.query(
                extract('month', User.date_create).label('month'),
                extract('year', User.date_create).label('year'),
                func.count(User.id).label('user_count')
            ).filter(
                User.date_create >= twelve_months_ago
            ).group_by(
                extract('year', User.date_create),
                extract('month', User.date_create)
            ).all()
            
            # Combiner les données
            result = []
            exam_dict = {(int(year), int(month)): count for month, year, count in exam_data}
            user_dict = {(int(year), int(month)): count for month, year, count in user_data}
            
            # Générer les 12 derniers mois
            current_date = datetime.utcnow()
            for i in range(12):
                date = current_date - timedelta(days=30*i)
                year, month = date.year, date.month
                month_name = date.strftime('%B %Y')
                
                result.append({
                    'month': month_name,
                    'exams': exam_dict.get((year, month), 0),
                    'users': user_dict.get((year, month), 0)
                })
            
            result.reverse()  # Ordre chronologique
        
        return result

@dashboard_ns.route("/activity/recent")
class DashboardRecentActivityResource(Resource):
    
    @jwt_required()
    def get(self):
        '''Récupérer l\'activité récente'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
        
        if user.role == 'Client':
            # Pour les clients, montrer leurs examens récents
            recent_exams = TCFExam.query.filter_by(
                id_user=user.id
            ).order_by(
                TCFExam.date_passage.desc()
            ).limit(5).all()
            
            result = []
            for exam in recent_exams:
                # Récupérer le nom du sujet
                subject = TCFSubject.query.get(exam.id_subject)
                subject_name = subject.name if subject else f"Sujet {exam.id_subject}"
                
                result.append({
                    'id': exam.id,
                    'title': f"Coach {subject_name}",
                    'description': f"Tâche {exam.id_task}",
                    'date': exam.date_passage.isoformat() if exam.date_passage else None,
                    'type': 'exam',
                    'score': exam.score or '0'
                })
        
        else:
            # Pour les admins, montrer l'activité globale récente
            recent_exams = TCFExam.query.order_by(
                TCFExam.date_passage.desc()
            ).limit(5).all()
            
            result = []
            for exam in recent_exams:
                # Récupérer les informations utilisateur et sujet
                exam_user = User.query.get(exam.id_user)
                subject = TCFSubject.query.get(exam.id_subject)
                
                user_name = exam_user.username if exam_user else f"Utilisateur {exam.id_user}"
                subject_name = subject.name if subject else f"Sujet {exam.id_subject}"
                
                result.append({
                    'id': exam.id,
                    'title': f"{user_name} - Coach {subject_name}",
                    'description': f"Tâche {exam.id_task}",
                    'date': exam.date_passage.isoformat() if exam.date_passage else None,
                    'type': 'exam',
                    'score': exam.score or '0'
                })
        
        return result