# ─────────────────────────────────────────────────────────────
# app.py  ―  Flask + Material Dashboard 통합 진입점
# 포트: 5558 (debug 모드)
# ─────────────────────────────────────────────────────────────
from pathlib import Path
from datetime import datetime, date
import pandas as pd

from flask import (
    Flask, render_template, Blueprint,
    request, redirect, url_for
)
from db_manager import DBManager   # ← 기존 DB 유틸

# ─────────────────────────────────────────────────────────────
# 1) 앱 & DB 매니저
# ─────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="pages", static_folder="assets")
db  = DBManager()

# ─────────────────────────────────────────────────────────────
# 2) 경로 상수 (app.py 기준)
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent            # …\flask
CSV_FILE = BASE_DIR / "data" / "workforce" / "korea_attendance.csv"

# ─────────────────────────────────────────────────────────────
# 3) 출근 성실도 블루프린트
# ─────────────────────────────────────────────────────────────
attendance_bp = Blueprint("attendance", __name__, url_prefix="")
@attendance_bp.route("/attendance")
def attendance_summary():
    df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")

    summary = (
        df.groupby("emp_name")
          .lateness_label
          .agg(total="count", late="sum")
          .reset_index()
    )
    summary["perf_pct"] = ((1 - summary["late"] / summary["total"]) * 100).round(1)

    records = summary.to_dict("records")
    return render_template("attendance_summary.html", records=records)

app.register_blueprint(attendance_bp)

# ─────────────────────────────────────────────────────────────
# 4) 작업 진행률 뷰
# ─────────────────────────────────────────────────────────────
@app.route("/progress")
def progress_dashboard():
    progress_data = db.get_progress_data()   # db_manager.py 쪽 구현
    return render_template("progress.html", progress_data=progress_data)

# ─────────────────────────────────────────────────────────────
# 5) 대시보드 기본/고정 라우트
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/billing")
def billing():
    inventory_data = db.get_inventory_status()
    return render_template("billing.html", inventory_data=inventory_data)

@app.route("/map")
def map_page():
    return render_template("map.html")

@app.route("/notifications")
def notifications():
    return render_template("notifications.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/sign-in")
def sign_in():
    return render_template("sign-in.html")

@app.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")

@app.route("/tables")
def tables():
    return render_template("tables.html")

@app.route("/rtl")
def rtl():
    return render_template("rtl.html")

# ─────────────────────────────────────────────────────────────
# 6) AJAX용 파셜 로드 섹션 (/load_section?section=…)
# ─────────────────────────────────────────────────────────────
@app.route("/load_section")
def load_partial_section():
    """JS에서 section=orders|logs|vendors|transactions 로 호출"""
    section = request.args.get('section')

    if section == 'order':                               # ← 복수형으로 통일
        work_orders = db.get_all_work_orders()
        return render_template('partials/work_orders.html',
                               work_orders=work_orders)

    elif section == 'logs':
        work_logs   = db.get_all_work_logs()
        work_orders = db.get_all_work_orders()
        return render_template('partials/work_logs.html',
                               work_logs=work_logs,
                               work_orders=work_orders)

    elif section == 'vendors':
        vendors = db.get_all_vendors()
        return render_template('partials/vendors.html',
                               vendors=vendors)

    elif section == 'transactions':
        transactions = db.get_all_material_transactions()
        vendors      = db.get_all_vendors()
        work_orders  = db.get_all_work_orders()
        return render_template('partials/transactions.html',
                               transactions=transactions,
                               vendors=vendors,
                               work_orders=work_orders)

    return "섹션 없음", 404

# ─────────────────────────────────────────────────────────────
# 7) CRUD 라우트 ― 작업지시 /order
# ─────────────────────────────────────────────────────────────
@app.route('/order', methods=['GET', 'POST'])
def work_order_page():
    if request.method == 'POST':
        form = request.form
        mode = form.get('mode')

        if mode == 'add':
            material_names = form.getlist('material_name[]')
            units          = form.getlist('unit[]')

            for name, unit in zip(material_names, units):
                if name.strip():
                    db.insert_work_order(
                        contract_number = form['contract_number'],
                        contract_name   = form['contract_name'],
                        site_number     = form['site_number'],
                        site_name       = form['site_name'],
                        process_name    = form['process_name'],
                        material_name   = name,
                        planned_quantity= float(form['planned_quantity'] or 0),
                        unit            = unit,
                        start_date      = form['start_date'],
                        end_date        = form['end_date']
                    )

        elif mode == 'edit':
            db.update_work_order(
                orders_seq       = form['orders_seq'],
                contract_number  = form['contract_number'],
                contract_name    = form['contract_name'],
                site_number      = form['site_number'],
                site_name        = form['site_name'],
                process_name     = form['process_name'],
                material_name    = form['material_name'],
                planned_quantity = float(form['planned_quantity'] or 0),
                unit             = form['unit'],
                start_date       = form['start_date'],
                end_date         = form['end_date']
            )
        return redirect(url_for('work_order_page'))

    # GET
    if request.args.get('delete_id'):
        db.delete_work_order(request.args['delete_id'])
        return redirect(url_for('work_order_page'))

    edit_id     = request.args.get('edit_id')
    work_order  = db.get_work_order_by_id(edit_id) if edit_id else None
    work_orders = db.get_all_work_orders()
    return render_template('partials/work_orders.html',
                           work_orders=work_orders,
                           edit_order=work_order)

# ─────────────────────────────────────────────────────────────
# 8) CRUD 라우트 ― 작업일지 /logs
# ─────────────────────────────────────────────────────────────
@app.route('/logs', methods=['GET', 'POST'])
def work_logs_page():
    if request.method == 'POST':
        form = request.form
        mode = form.get('mode')

        if mode == 'add':
            material_names = form.getlist('material_name[]')
            quantities     = form.getlist('quantity_used[]')
            units          = form.getlist('unit[]')

            for name, qty, unit in zip(material_names, quantities, units):
                if name.strip():
                    db.insert_work_log(
                        orders_seq       = form['orders_seq'],
                        work_date        = form['work_date'],
                        site_number      = form['site_number'],
                        site_name        = form['site_name'],
                        task_description = form['task_description'],
                        foreman          = form['foreman'],
                        workers          = form['workers'],
                        material_name    = name,
                        quantity_used    = float(qty or 0),
                        unit             = unit,
                        img_path         = form.get('img_path', '')
                    )

        elif mode == 'edit':
            db.update_work_log(
                logs_seq         = form['logs_seq'],
                orders_seq       = form['orders_seq'],
                work_date        = form['work_date'],
                site_number      = form['site_number'],
                site_name        = form['site_name'],
                task_description = form['task_description'],
                foreman          = form['foreman'],
                workers          = form['workers'],
                material_name    = form['material_name'],
                quantity_used    = float(form['quantity_used'] or 0),
                unit             = form['unit'],
                img_path         = form['img_path']
            )
        return redirect(url_for('work_logs_page'))

    # GET
    if request.args.get('delete_id'):
        db.delete_work_log(request.args['delete_id'])
        return redirect(url_for('work_logs_page'))

    edit_id     = request.args.get('edit_id')
    edit_log    = db.get_work_log_by_id(edit_id) if edit_id else None
    work_logs   = db.get_all_work_logs()
    work_orders = db.get_all_work_orders()
    return render_template('partials/work_logs.html',
                           work_logs=work_logs,
                           edit_log=edit_log,
                           work_orders=work_orders)

# ─────────────────────────────────────────────────────────────
# 9) CRUD 라우트 ― 공급업체 /vendors
# ─────────────────────────────────────────────────────────────
@app.route('/vendors', methods=['GET', 'POST'])
def vendors_page():
    if request.method == 'POST':
        form = request.form
        mode = form.get('mode')

        if mode == 'add':
            db.insert_vendor(
                vendors_name   = form['vendors_name'],
                contact_person = form['contact_person'],
                phone          = form['phone'],
                address        = form['address'],
                email          = form['email']
            )
        elif mode == 'edit':
            db.update_vendor(
                vendors_seq    = form['vendors_seq'],
                vendors_name   = form['vendors_name'],
                contact_person = form['contact_person'],
                phone          = form['phone'],
                address        = form['address'],
                email          = form['email']
            )
        return redirect(url_for('vendors_page'))

    # GET
    if request.args.get('delete_id'):
        db.delete_vendor(request.args['delete_id'])
        return redirect(url_for('vendors_page'))

    edit_id      = request.args.get('edit_id')
    edit_vendor  = db.get_vendor_by_id(edit_id) if edit_id else None
    vendors      = db.get_all_vendors()
    return render_template('partials/vendors.html',
                           vendors=vendors,
                           edit_vendor=edit_vendor)

# ─────────────────────────────────────────────────────────────
# 10) CRUD 라우트 ― 자재 거래 /transactions
# ─────────────────────────────────────────────────────────────
@app.route('/transactions', methods=['GET', 'POST'])
def transactions_page():
    if request.method == 'POST':
        form = request.form
        mode = form.get('mode')

        if mode == 'add_multi':
            materials = []
            for n, q, u, p, i in zip(
                form.getlist('material_name[]'),
                form.getlist('quantity[]'),
                form.getlist('unit[]'),
                form.getlist('price[]'),
                form.getlist('img_path[]')
            ):
                if n.strip():
                    materials.append({
                        'material_name': n,
                        'quantity'     : float(q or 0),
                        'unit'         : u,
                        'price'        : float(p or 0),
                        'img_path'     : i
                    })

            db.insert_material_transactions(
                transaction_date = form['transaction_date'],
                vendors_seq      = form['vendors_seq'],
                orders_seq       = form.get('orders_seq'),
                materials        = materials
            )

        elif mode == 'edit':
            db.update_material_transaction(
                trans_seq        = form['trans_seq'],
                transaction_date = form['transaction_date'],
                vendors_seq      = form['vendors_seq'],
                material_name    = form['material_name'],
                quantity         = float(form['quantity'] or 0),
                unit             = form['unit'],
                price            = float(form['price'] or 0),
                orders_seq       = form['orders_seq'],
                img_path         = form['img_path']
            )

        return redirect(url_for('transactions_page'))

    # GET
    if request.args.get('delete_id'):
        db.delete_material_transaction(request.args['delete_id'])
        return redirect(url_for('transactions_page'))

    edit_id      = request.args.get('edit_id')
    edit_trans   = db.get_transaction_by_id(edit_id) if edit_id else None
    transactions = db.get_all_material_transactions()
    vendors      = db.get_all_vendors()
    work_orders  = db.get_all_work_orders()
    return render_template('partials/transactions.html',
                           transactions     = transactions,
                           edit_transaction = edit_trans,
                           vendors          = vendors,
                           work_orders      = work_orders)

# ─────────────────────────────────────────────────────────────
# 11) 앱 실행
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("CSV_FILE →", CSV_FILE)          # 경로 확인용
    print("Exists?  →", CSV_FILE.exists()) # True 여야 정상
    app.run(debug=True, port=5558)