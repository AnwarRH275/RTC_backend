import os
import sqlite3
from contextlib import closing

from app import app
from models.exts import db

# Import models (cible MariaDB)
from models.model import User
from models.subscription_pack_model import SubscriptionPack, PackFeature
from models.order_model import Order
from models.tcf_model import TCFSubject, TCFTask, TCFDocument
from models.tcf_exam_model import TCFExam
from models.tcf_attempt_model import TCFAttempt
from models.tcf_model_oral import TCFOralSubject, TCFOralTask

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'dev.db')


def table_exists_sqlite(cur, table_name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cur.fetchone() is not None


def get_columns(cur, table_name: str):
    cols = []
    cur.execute(f"PRAGMA table_info({table_name})")
    for row in cur.fetchall():
        cols.append(row[1])
    return set(cols)


def migrate_users(cur):
    if not table_exists_sqlite(cur, 'user'):
        print('Table user introuvable dans SQLite, saut...')
        return
    cols = get_columns(cur, 'user')
    cur.execute('SELECT * FROM user')
    rows = cur.fetchall()
    # Récupérer l'ordre des colonnes de la table
    cur.execute('PRAGMA table_info(user)')
    col_order = [r[1] for r in cur.fetchall()]

    inserted = 0
    updated = 0
    with app.app_context():
        for row in rows:
            record = dict(zip(col_order, row))
            # Vérifier si un utilisateur avec le même id existe déjà
            existing_by_id = User.query.get(record.get('id'))
            if existing_by_id:
                # Mettre à jour les champs pour éviter les conflits de clé primaire
                existing_by_id.username = record.get('username')
                existing_by_id.email = record.get('email')
                existing_by_id.password = record.get('password')
                existing_by_id.nom = record.get('nom')
                existing_by_id.prenom = record.get('prenom')
                existing_by_id.tel = record.get('tel')
                existing_by_id.sexe = record.get('sexe')
                existing_by_id.date_naissance = record.get('date_naissance')
                existing_by_id.date_create = record.get('date_create')
                existing_by_id.subscription_plan = record.get('subscription_plan')
                existing_by_id.payment_status = record.get('payment_status')
                existing_by_id.payment_id = record.get('payment_id')
                existing_by_id.role = record.get('role') or 'client'
                existing_by_id.sold = record.get('sold') or 0.0
                existing_by_id.total_sold = record.get('total_sold') or 0.0
                existing_by_id.reset_token = record.get('reset_token')
                existing_by_id.reset_token_expires = record.get('reset_token_expires')
                existing_by_id.created_by = record.get('created_by') if 'created_by' in cols else None
                updated += 1
                continue

            # Éviter les doublons par username si l'id n'existe pas
            existing_by_username = db.session.query(User.id).filter_by(username=record.get('username')).first()
            if existing_by_username:
                # Mettre à jour l'utilisateur trouvé par username
                user = User.query.get(existing_by_username[0])
                user.email = record.get('email')
                user.password = record.get('password')
                user.nom = record.get('nom')
                user.prenom = record.get('prenom')
                user.tel = record.get('tel')
                user.sexe = record.get('sexe')
                user.date_naissance = record.get('date_naissance')
                user.date_create = record.get('date_create')
                user.subscription_plan = record.get('subscription_plan')
                user.payment_status = record.get('payment_status')
                user.payment_id = record.get('payment_id')
                user.role = record.get('role') or 'client'
                user.sold = record.get('sold') or 0.0
                user.total_sold = record.get('total_sold') or 0.0
                user.reset_token = record.get('reset_token')
                user.reset_token_expires = record.get('reset_token_expires')
                user.created_by = record.get('created_by') if 'created_by' in cols else None
                updated += 1
                continue

            # Sinon, insérer un nouvel utilisateur en préservant l'ID
            user = User(
                id=record.get('id'),
                username=record.get('username'),
                email=record.get('email'),
                password=record.get('password'),
                nom=record.get('nom'),
                prenom=record.get('prenom'),
                tel=record.get('tel'),
                sexe=record.get('sexe'),
                date_naissance=record.get('date_naissance'),
                date_create=record.get('date_create'),
                subscription_plan=record.get('subscription_plan'),
                payment_status=record.get('payment_status'),
                payment_id=record.get('payment_id'),
                role=record.get('role') or 'client',
                sold=record.get('sold') or 0.0,
                total_sold=record.get('total_sold') or 0.0,
                reset_token=record.get('reset_token'),
                reset_token_expires=record.get('reset_token_expires'),
                created_by=record.get('created_by') if 'created_by' in cols else None,
            )
            db.session.add(user)
            inserted += 1
        db.session.commit()
    print(f"Utilisateurs migrés: {inserted}, mis à jour: {updated}")


def migrate_subscription_packs_and_features(cur):
    if not table_exists_sqlite(cur, 'subscription_packs'):
        print('Table subscription_packs introuvable, saut...')
        return
    cur.execute('PRAGMA table_info(subscription_packs)')
    pack_cols = [r[1] for r in cur.fetchall()]
    cur.execute('SELECT * FROM subscription_packs')
    pack_rows = cur.fetchall()

    inserted_packs = 0
    with app.app_context():
        for row in pack_rows:
            record = dict(zip(pack_cols, row))
            existing = SubscriptionPack.query.filter_by(pack_id=record.get('pack_id')).first()
            if existing:
                continue
            pack = SubscriptionPack(
                id=record.get('id'),
                pack_id=record.get('pack_id'),
                name=record.get('name'),
                price=record.get('price'),
                price_in_cents=record.get('price_in_cents'),
                usages=record.get('usages'),
                color=record.get('color'),
                is_popular=record.get('is_popular'),
                stripe_product_id=record.get('stripe_product_id'),
                header_gradient_start=record.get('header_gradient_start'),
                header_gradient_end=record.get('header_gradient_end'),
                button_gradient_start=record.get('button_gradient_start'),
                button_gradient_end=record.get('button_gradient_end'),
                button_hover_gradient_start=record.get('button_hover_gradient_start'),
                button_hover_gradient_end=record.get('button_hover_gradient_end'),
                button_text=record.get('button_text') or 'Payer maintenant',
                is_active=record.get('is_active'),
                created_at=record.get('created_at'),
                updated_at=record.get('updated_at'),
            )
            db.session.add(pack)
            inserted_packs += 1
        db.session.commit()
    print(f"Packs migrés: {inserted_packs}")

    # Features
    if not table_exists_sqlite(cur, 'pack_features'):
        print('Table pack_features introuvable, saut...')
        return
    cur.execute('PRAGMA table_info(pack_features)')
    feat_cols = [r[1] for r in cur.fetchall()]
    cur.execute('SELECT * FROM pack_features')
    feat_rows = cur.fetchall()

    inserted_feats = 0
    with app.app_context():
        for row in feat_rows:
            record = dict(zip(feat_cols, row))
            feature = PackFeature(
                id=record.get('id'),
                pack_id=record.get('pack_id'),
                feature_text=record.get('feature_text'),
                order_index=record.get('order_index'),
                is_active=record.get('is_active'),
                created_at=record.get('created_at'),
            )
            db.session.add(feature)
            inserted_feats += 1
        db.session.commit()
    print(f"Fonctionnalités migrées: {inserted_feats}")


def migrate_tcf(cur):
    # Subjects
    if table_exists_sqlite(cur, 'tcf_subject'):
        cur.execute('PRAGMA table_info(tcf_subject)')
        cols = [r[1] for r in cur.fetchall()]
        cur.execute('SELECT * FROM tcf_subject')
        rows = cur.fetchall()
        with app.app_context():
            for row in rows:
                rec = dict(zip(cols, row))
                if TCFSubject.query.get(rec.get('id')):
                    continue
                obj = TCFSubject(
                    id=rec.get('id'), name=rec.get('name'), date=rec.get('date'), status=rec.get('status'),
                    duration=rec.get('duration'), subject_type=rec.get('subject_type'), description=rec.get('description'),
                    combination=rec.get('combination'),
                )
                db.session.add(obj)
            db.session.commit()
        print(f"TCFSubject migrés: {len(rows)}")

    # Tasks
    if table_exists_sqlite(cur, 'tcf_task'):
        cur.execute('PRAGMA table_info(tcf_task)')
        cols = [r[1] for r in cur.fetchall()]
        cur.execute('SELECT * FROM tcf_task')
        rows = cur.fetchall()
        with app.app_context():
            for row in rows:
                rec = dict(zip(cols, row))
                if TCFTask.query.get(rec.get('id')):
                    continue
                obj = TCFTask(
                    id=rec.get('id'), title=rec.get('title'), structure=rec.get('structure'), instructions=rec.get('instructions'),
                    min_word_count=rec.get('min_word_count'), max_word_count=rec.get('max_word_count'), duration=rec.get('duration'),
                    subject_id=rec.get('subject_id'),
                )
                db.session.add(obj)
            db.session.commit()
        print(f"TCFTask migrés: {len(rows)}")

    # Documents
    if table_exists_sqlite(cur, 'tcf_document'):
        cur.execute('PRAGMA table_info(tcf_document)')
        cols = [r[1] for r in cur.fetchall()]
        cur.execute('SELECT * FROM tcf_document')
        rows = cur.fetchall()
        with app.app_context():
            for row in rows:
                rec = dict(zip(cols, row))
                if TCFDocument.query.get(rec.get('id')):
                    continue
                obj = TCFDocument(id=rec.get('id'), content=rec.get('content'), task_id=rec.get('task_id'))
                db.session.add(obj)
            db.session.commit()
        print(f"TCFDocument migrés: {len(rows)}")

    # Exams
    if table_exists_sqlite(cur, 'tcf_exam'):
        cur.execute('PRAGMA table_info(tcf_exam)')
        cols = [r[1] for r in cur.fetchall()]
        cur.execute('SELECT * FROM tcf_exam')
        rows = cur.fetchall()
        with app.app_context():
            for row in rows:
                rec = dict(zip(cols, row))
                if TCFExam.query.get(rec.get('id')):
                    continue
                obj = TCFExam(
                    id=rec.get('id'), id_user=rec.get('id_user'), id_subject=rec.get('id_subject'), id_task=rec.get('id_task'),
                    reponse_utilisateur=rec.get('reponse_utilisateur'), score=rec.get('score'), reponse_ia=rec.get('reponse_ia'),
                    points_fort=rec.get('points_fort'), point_faible=rec.get('point_faible'), traduction_reponse_ia=rec.get('traduction_reponse_ia'),
                    type_exam=rec.get('type_exam'), date_passage=rec.get('date_passage'),
                )
                db.session.add(obj)
            db.session.commit()
        print(f"TCFExam migrés: {len(rows)}")

    # Attempts
    if table_exists_sqlite(cur, 'tcf_attempt'):
        cur.execute('PRAGMA table_info(tcf_attempt)')
        cols = [r[1] for r in cur.fetchall()]
        cur.execute('SELECT * FROM tcf_attempt')
        rows = cur.fetchall()
        with app.app_context():
            for row in rows:
                rec = dict(zip(cols, row))
                if TCFAttempt.query.get(rec.get('id')):
                    continue
                obj = TCFAttempt(
                    id=rec.get('id'), id_user=rec.get('id_user'), id_subject=rec.get('id_subject'), id_task=rec.get('id_task'),
                    text_user=rec.get('text_user'), note_user=rec.get('note_user'), note_ia=rec.get('note_ia'), translate_text=rec.get('translate_text'),
                    note_moyenne=rec.get('note_moyenne'), time_submit=rec.get('time_submit'), type_exam=rec.get('type_exam'),
                )
                db.session.add(obj)
            db.session.commit()
        print(f"TCFAttempt migrés: {len(rows)}")

    # Oral Subject & Task
    if table_exists_sqlite(cur, 'tcf_oral_subject'):
        cur.execute('PRAGMA table_info(tcf_oral_subject)')
        cols = [r[1] for r in cur.fetchall()]
        cur.execute('SELECT * FROM tcf_oral_subject')
        rows = cur.fetchall()
        with app.app_context():
            for row in rows:
                rec = dict(zip(cols, row))
                if TCFOralSubject.query.get(rec.get('id')):
                    continue
                obj = TCFOralSubject(
                    id=rec.get('id'), name=rec.get('name'), date=rec.get('date'), status=rec.get('status'), duration=rec.get('duration'),
                    subject_type=rec.get('subject_type'), description=rec.get('description'), combination=rec.get('combination'),
                )
                db.session.add(obj)
            db.session.commit()
        print(f"TCFOralSubject migrés: {len(rows)}")

    if table_exists_sqlite(cur, 'tcf_oral_task'):
        cur.execute('PRAGMA table_info(tcf_oral_task)')
        cols = [r[1] for r in cur.fetchall()]
        cur.execute('SELECT * FROM tcf_oral_task')
        rows = cur.fetchall()
        with app.app_context():
            for row in rows:
                rec = dict(zip(cols, row))
                if TCFOralTask.query.get(rec.get('id')):
                    continue
                obj = TCFOralTask(
                    id=rec.get('id'), title=rec.get('title'), task_type=rec.get('task_type'), objective=rec.get('objective'), trigger=rec.get('trigger'),
                    evaluation_criteria=rec.get('evaluation_criteria'), duration=rec.get('duration'), points=rec.get('points'),
                    preparation_time=rec.get('preparation_time'), roleplay_scenario=rec.get('roleplay_scenario'), subject_id=rec.get('subject_id'),
                )
                db.session.add(obj)
            db.session.commit()
        print(f"TCFOralTask migrés: {len(rows)}")


def migrate_orders(cur):
    if not table_exists_sqlite(cur, 'orders'):
        print('Table orders introuvable, saut...')
        return
    cur.execute('PRAGMA table_info(orders)')
    cols = [r[1] for r in cur.fetchall()]
    cur.execute('SELECT * FROM orders')
    rows = cur.fetchall()
    with app.app_context():
        for row in rows:
            rec = dict(zip(cols, row))
            if Order.query.get(rec.get('id')):
                continue
            obj = Order(
                id=rec.get('id'), order_number=rec.get('order_number'), user_id=rec.get('user_id'), subscription_plan=rec.get('subscription_plan'),
                amount=rec.get('amount'), currency=rec.get('currency'), status=rec.get('status'), payment_status=rec.get('payment_status'),
                payment_method=rec.get('payment_method'), stripe_session_id=rec.get('stripe_session_id'), stripe_payment_intent_id=rec.get('stripe_payment_intent_id'),
                stripe_charge_id=rec.get('stripe_charge_id'), customer_email=rec.get('customer_email'), customer_name=rec.get('customer_name'), customer_phone=rec.get('customer_phone'),
                notes=rec.get('notes'), refund_reason=rec.get('refund_reason'), cancelled_by=rec.get('cancelled_by'),
                created_at=rec.get('created_at'), updated_at=rec.get('updated_at'), paid_at=rec.get('paid_at'), cancelled_at=rec.get('cancelled_at'), refunded_at=rec.get('refunded_at'),
            )
            db.session.add(obj)
        db.session.commit()
    print(f"Orders migrés: {len(rows)}")


def main():
    if not os.path.exists(SQLITE_PATH):
        raise FileNotFoundError(f"SQLite dev.db introuvable à {SQLITE_PATH}")

    with closing(sqlite3.connect(SQLITE_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        print('--- Début migration depuis SQLite dev.db vers MariaDB ---')
        migrate_users(cur)
        migrate_subscription_packs_and_features(cur)
        migrate_tcf(cur)
        migrate_orders(cur)
        print('--- Migration terminée ---')


if __name__ == '__main__':
    # S'assurer que l'application est configurée pour MariaDB via DATABASE_URL
    app.app_context().push()
    main()