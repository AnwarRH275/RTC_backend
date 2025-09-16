from flask import request, jsonify, make_response, current_app
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.model import User
from models.order_model import Order
from models.subscription_pack_model import SubscriptionPack
from models.exts import db
from datetime import datetime, timedelta
import stripe
from services.auth.stripe import init_stripe

# Créer un namespace pour les routes d'administration des commandes
order_admin_ns = Namespace('order-admin', description='Administration des commandes et transactions')

# Modèles pour la documentation API
order_model = order_admin_ns.model(
    "Order",
    {
        "id": fields.Integer(description="ID de la commande"),
        "orderNumber": fields.String(description="Numéro de commande"),
        "userId": fields.Integer(description="ID de l'utilisateur"),
        "subscriptionPlan": fields.String(description="Plan d'abonnement"),
        "amount": fields.Float(description="Montant"),
        "currency": fields.String(description="Devise"),
        "status": fields.String(description="Statut de la commande"),
        "paymentStatus": fields.String(description="Statut du paiement"),
        "customerEmail": fields.String(description="Email du client"),
        "customerName": fields.String(description="Nom du client"),
        "createdAt": fields.String(description="Date de création"),
        "paidAt": fields.String(description="Date de paiement"),
    }
)

order_create_model = order_admin_ns.model(
    "OrderCreate",
    {
        "userId": fields.Integer(required=True, description="ID de l'utilisateur"),
        "subscriptionPlan": fields.String(required=True, description="Plan d'abonnement"),
        "amount": fields.Float(required=True, description="Montant"),
        "currency": fields.String(description="Devise (défaut: USD)"),
        "paymentMethod": fields.String(description="Méthode de paiement"),
        "notes": fields.String(description="Notes administratives"),
    }
)

order_update_model = order_admin_ns.model(
    "OrderUpdate",
    {
        "status": fields.String(description="Nouveau statut"),
        "notes": fields.String(description="Notes administratives"),
        "refundReason": fields.String(description="Raison du remboursement"),
    }
)

order_cancel_model = order_admin_ns.model(
    "OrderCancel",
    {
        "reason": fields.String(description="Raison de l'annulation"),
        "resetUserBalance": fields.Boolean(description="Remettre le solde client à zéro"),
    }
)

stats_model = order_admin_ns.model(
    "OrderStats",
    {
        "totalRevenue": fields.Float(description="Revenus totaux"),
        "totalOrders": fields.Integer(description="Nombre total de commandes"),
        "averageOrderValue": fields.Float(description="Valeur moyenne des commandes"),
        "planStats": fields.Raw(description="Statistiques par plan"),
    }
)


def admin_required(f):
    """Décorateur pour vérifier les droits d'administration"""
    def decorated_function(*args, **kwargs):
        current_username = get_jwt_identity()
        user = User.query.filter_by(username=current_username).first()
        if not user or user.role != 'admin':
            return make_response(jsonify({"error": "Accès refusé. Droits d'administration requis."}), 403)
        return f(*args, **kwargs)
    return decorated_function


@order_admin_ns.route('/orders')
class OrderList(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        """Récupérer toutes les commandes avec filtres optionnels"""
        try:
            # Paramètres de filtrage
            status = request.args.get('status')
            user_id = request.args.get('userId')
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            plan = request.args.get('plan')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('perPage', 50))
            
            # Construire la requête
            query = Order.query
            
            if status:
                query = query.filter(Order.status == status)
            if user_id:
                query = query.filter(Order.user_id == user_id)
            if plan:
                query = query.filter(Order.subscription_plan == plan)
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Order.created_at >= start_dt)
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Order.created_at <= end_dt)
            
            # Ordonner par date de création décroissante
            query = query.order_by(Order.created_at.desc())
            
            # Pagination
            orders = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return make_response(jsonify({
                "orders": [order.to_dict() for order in orders.items],
                "pagination": {
                    "page": orders.page,
                    "pages": orders.pages,
                    "perPage": orders.per_page,
                    "total": orders.total
                }
            }), 200)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des commandes: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)
    
    @jwt_required()
    @admin_required
    @order_admin_ns.expect(order_create_model)
    def post(self):
        """Créer une nouvelle commande manuellement"""
        try:
            data = request.get_json()
            current_user_id = get_jwt_identity()
            
            # Vérifier que l'utilisateur existe
            user = User.query.get(data['userId'])
            if not user:
                return make_response(jsonify({"error": "Utilisateur introuvable"}), 404)
            
            # Créer la commande
            order = Order(
                user_id=data['userId'],
                subscription_plan=data['subscriptionPlan'],
                amount=data['amount'],
                currency=data.get('currency', 'USD'),
                payment_method=data.get('paymentMethod', 'manual'),
                customer_email=user.email,
                customer_name=f"{user.prenom or ''} {user.nom or ''}".strip(),
                customer_phone=user.tel,
                notes=data.get('notes')
            )
            
            db.session.add(order)
            db.session.commit()
            
            return make_response(jsonify({
                "message": "Commande créée avec succès",
                "order": order.to_dict()
            }), 201)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la création de la commande: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)


@order_admin_ns.route('/orders/<int:order_id>')
class OrderDetail(Resource):
    @jwt_required()
    @admin_required
    def get(self, order_id):
        """Récupérer les détails d'une commande"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return make_response(jsonify({"error": "Commande introuvable"}), 404)
            
            return make_response(jsonify(order.to_dict()), 200)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération de la commande: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)
    
    @jwt_required()
    @admin_required
    @order_admin_ns.expect(order_update_model)
    def put(self, order_id):
        """Mettre à jour une commande"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return make_response(jsonify({"error": "Commande introuvable"}), 404)
            
            data = request.get_json()
            current_user_id = get_jwt_identity()
            
            # Mettre à jour les champs
            if 'status' in data:
                order.update_status(data['status'], current_user_id, data.get('notes'))
            
            if 'notes' in data:
                order.notes = data['notes']
            
            if 'refundReason' in data:
                order.refund_reason = data['refundReason']
            
            order.updated_at = datetime.utcnow()
            db.session.commit()
            
            return make_response(jsonify({
                "message": "Commande mise à jour avec succès",
                "order": order.to_dict()
            }), 200)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la mise à jour de la commande: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)
    
    @jwt_required()
    @admin_required
    def delete(self, order_id):
        """Supprimer une commande (attention: action irréversible)"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return make_response(jsonify({"error": "Commande introuvable"}), 404)
            
            order.delete()
            
            return make_response(jsonify({"message": "Commande supprimée avec succès"}), 200)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la suppression de la commande: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)


@order_admin_ns.route('/orders/<int:order_id>/cancel')
class OrderCancel(Resource):
    @jwt_required()
    @admin_required
    @order_admin_ns.expect(order_cancel_model)
    def post(self, order_id):
        """Annuler une commande et optionnellement remettre le solde client à zéro"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return make_response(jsonify({"error": "Commande introuvable"}), 404)
            
            data = request.get_json() or {}
            current_user_id = get_jwt_identity()
            
            reason = data.get('reason')
            reset_balance = data.get('resetUserBalance', False)
            
            # Check if order can be cancelled
            if order.status == 'cancelled':
                return make_response(jsonify({"error": "Cette commande est déjà annulée"}), 400)
            
            if order.status == 'completed':
                return make_response(jsonify({"error": "Impossible d'annuler une commande terminée"}), 400)
            
            # Update order status directly
            order.status = 'cancelled'
            order.payment_status = 'cancelled'
            order.cancelled_by = current_user_id
            order.cancelled_at = datetime.utcnow()
            
            if reason:
                order.refund_reason = reason
            
            
            user = User.query.get(order.user_id)
            if user:
                user.sold = 0.0
                user.total_sold = 0.0
                db.session.add(user)
            
            db.session.add(order)
            db.session.commit()
            
            return make_response(jsonify({
                "message": "Commande annulée avec succès",
                "order": order.to_dict()
            }), 200)
                
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'annulation de la commande: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)


@order_admin_ns.route('/orders/<int:order_id>/refund')
class OrderRefund(Resource):
    @jwt_required()
    @admin_required
    def post(self, order_id):
        """Rembourser une commande via Stripe"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return make_response(jsonify({"error": "Commande introuvable"}), 404)
            
            if order.status != 'paid':
                return make_response(jsonify({"error": "Seules les commandes payées peuvent être remboursées"}), 400)
            
            if not order.stripe_charge_id and not order.stripe_payment_intent_id:
                return make_response(jsonify({"error": "Aucune information de paiement Stripe trouvée"}), 400)
            
            # Initialiser Stripe
            init_stripe()
            
            data = request.get_json() or {}
            reason = data.get('reason', 'Remboursement administratif')
            current_user_id = get_jwt_identity()
            
            # Effectuer le remboursement via Stripe
            try:
                if order.stripe_payment_intent_id:
                    refund = stripe.Refund.create(
                        payment_intent=order.stripe_payment_intent_id,
                        reason='requested_by_customer'
                    )
                elif order.stripe_charge_id:
                    refund = stripe.Refund.create(
                        charge=order.stripe_charge_id,
                        reason='requested_by_customer'
                    )
                
                # Mettre à jour la commande
                order.status = 'refunded'
                order.payment_status = 'refunded'
                order.refund_reason = reason
                order.refunded_at = datetime.utcnow()
                order.cancelled_by = current_user_id
                order.updated_at = datetime.utcnow()
                
                # Remettre le solde client à zéro
                if order.user:
                    order.user.sold = 0.0
                    order.user.total_sold = 0.0
                
                db.session.commit()
                
                return make_response(jsonify({
                    "message": "Commande remboursée avec succès",
                    "refundId": refund.id,
                    "order": order.to_dict()
                }), 200)
                
            except stripe.error.StripeError as e:
                current_app.logger.error(f"Erreur Stripe lors du remboursement: {str(e)}")
                return make_response(jsonify({"error": f"Erreur de remboursement: {str(e)}"}), 400)
                
        except Exception as e:
            current_app.logger.error(f"Erreur lors du remboursement de la commande: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)


@order_admin_ns.route('/stats')
class OrderStats(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        """Récupérer les statistiques des commandes"""
        try:
            # Paramètres de date
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Récupérer les statistiques directement
            query = Order.query.filter(Order.status.in_(['paid', 'completed']))
            if start_dt:
                query = query.filter(Order.created_at >= start_dt)
            if end_dt:
                query = query.filter(Order.created_at <= end_dt)
            
            orders = query.all()
            total_revenue = sum(order.amount for order in orders)
            total_orders = len(orders)
            
            plans_stats = {}
            for order in orders:
                plan = order.subscription_plan
                if plan not in plans_stats:
                    plans_stats[plan] = {'count': 0, 'revenue': 0}
                plans_stats[plan]['count'] += 1
                plans_stats[plan]['revenue'] += order.amount
            
            stats = {
                'totalRevenue': total_revenue,
                'totalOrders': total_orders,
                'averageOrderValue': total_revenue / total_orders if total_orders > 0 else 0,
                'planStats': plans_stats
            }
            
            # Ajouter des statistiques supplémentaires
            query = Order.query
            if start_dt:
                query = query.filter(Order.created_at >= start_dt)
            if end_dt:
                query = query.filter(Order.created_at <= end_dt)
            
            # Statistiques par statut
            status_stats = {}
            for status in ['pending', 'paid', 'failed', 'cancelled', 'refunded']:
                count = query.filter(Order.status == status).count()
                status_stats[status] = count
            
            # Statistiques mensuelles (derniers 12 mois)
            monthly_stats = []
            for i in range(12):
                month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_orders = Order.query.filter(
                    Order.created_at >= month_start,
                    Order.created_at <= month_end,
                    Order.status == 'paid'
                ).all()
                
                monthly_revenue = sum(order.amount for order in month_orders)
                monthly_stats.insert(0, {
                    'month': month_start.strftime('%Y-%m'),
                    'revenue': monthly_revenue,
                    'orders': len(month_orders)
                })
            
            stats.update({
                'statusStats': status_stats,
                'monthlyStats': monthly_stats
            })
            
            return make_response(jsonify(stats), 200)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)


@order_admin_ns.route('/orders/export')
class OrderExport(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        """Exporter les commandes au format CSV"""
        try:
            # Paramètres de filtrage (mêmes que pour la liste)
            status = request.args.get('status')
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            
            query = Order.query
            
            if status:
                query = query.filter(Order.status == status)
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Order.created_at >= start_dt)
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Order.created_at <= end_dt)
            
            orders = query.order_by(Order.created_at.desc()).all()
            
            # Générer le CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            writer.writerow([
                'Numéro de commande', 'Date', 'Client', 'Email', 'Plan', 
                'Montant', 'Devise', 'Statut', 'Statut paiement', 'Méthode paiement'
            ])
            
            # Données
            for order in orders:
                writer.writerow([
                    order.order_number,
                    order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    order.customer_name or '',
                    order.customer_email,
                    order.subscription_plan,
                    order.amount,
                    order.currency,
                    order.status,
                    order.payment_status,
                    order.payment_method or ''
                ])
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=commandes_{datetime.now().strftime("%Y%m%d")}.csv'
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'export des commandes: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)