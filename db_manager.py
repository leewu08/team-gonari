import cx_Oracle
from datetime import datetime, date


class DBManager:
    # ─────────────────────────────────────────────
    # 0) 연결 헬퍼
    # ─────────────────────────────────────────────
    def __init__(self):
        self.connection = None          # cx_Oracle.Connection
        self.cursor     = None          # cx_Oracle.Cursor

    def connect(self):
        """필요할 때 연결·커서 생성(이미 있으면 재사용)"""
        if self.connection is None:
            dsn = cx_Oracle.makedsn("10.0.66.42", 1521, service_name="xe")
            self.connection = cx_Oracle.connect(
                user="sauser",
                password="0000",
                dsn=dsn,
                encoding="UTF-8"
            )
        if self.cursor is None:
            self.cursor = self.connection.cursor()

    def disconnect(self):
        """커서 → 연결 순서로 닫고 초기화"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    # ─────────────────────────────────────────────
    # 공통 SELECT → list[dict]
    # ─────────────────────────────────────────────
    def fetch_all(self, sql: str, params: dict | None = None):
        self.connect()
        cur = self.connection.cursor()
        cur.execute(sql, params or {})
        cols = [c[0].lower() for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        self.disconnect()
        return rows

    # ============================================================
    # 1) work_orders CRUD
    # ============================================================
    def insert_work_order(self, contract_number, contract_name, site_number, site_name,
                          process_name, material_name, planned_quantity, unit,
                          start_date, end_date):
        try:
            self.connect()
            sql = """
                INSERT INTO work_orders (
                    orders_seq, contract_number, contract_name, site_number,
                    site_name, process_name, material_name, planned_quantity,
                    unit, start_date, end_date
                ) VALUES (
                    seq_work_orders.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10
                )
            """
            self.cursor.execute(sql, (
                contract_number, contract_name, site_number, site_name,
                process_name, material_name, planned_quantity, unit,
                start_date or datetime.now(), end_date or datetime.now()
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("작업지시 insert 실패:", e)
            return False
        finally:
            self.disconnect()

    def get_all_work_orders(self):
        return self.fetch_all(
            "SELECT * FROM work_orders ORDER BY orders_seq DESC"
        )

    def get_work_order_by_id(self, orders_seq):
        rows = self.fetch_all(
            "SELECT * FROM work_orders WHERE orders_seq = :id",
            {"id": orders_seq}
        )
        return rows[0] if rows else None

    def update_work_order(self, orders_seq, contract_number, contract_name, site_number,
                          site_name, process_name, material_name, planned_quantity,
                          unit, start_date, end_date):
        try:
            self.connect()
            sql = """
                UPDATE work_orders SET
                    contract_number   = :1,
                    contract_name     = :2,
                    site_number       = :3,
                    site_name         = :4,
                    process_name      = :5,
                    material_name     = :6,
                    planned_quantity  = :7,
                    unit              = :8,
                    start_date        = :9,
                    end_date          = :10
                WHERE orders_seq      = :11
            """
            self.cursor.execute(sql, (
                contract_number, contract_name, site_number, site_name,
                process_name, material_name, planned_quantity, unit,
                start_date, end_date, orders_seq
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("작업지시 수정 실패:", e)
            return False
        finally:
            self.disconnect()

    def delete_work_order(self, orders_seq):
        try:
            self.connect()
            self.cursor.execute("DELETE FROM work_logs            WHERE orders_seq = :1", (orders_seq,))
            self.cursor.execute("DELETE FROM material_transactions WHERE orders_seq = :1", (orders_seq,))
            self.cursor.execute("DELETE FROM work_orders          WHERE orders_seq = :1", (orders_seq,))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("작업지시 삭제 실패:", e)
            return False
        finally:
            self.disconnect()

    # ============================================================
    # 2) work_logs CRUD
    # ============================================================
    def insert_work_log(self, orders_seq, work_date, site_number, site_name,
                        task_description, foreman, workers, material_name,
                        quantity_used, unit, img_path):
        try:
            self.connect()
            sql = """
                INSERT INTO work_logs (
                    logs_seq, orders_seq, work_date, site_number, site_name,
                    task_description, foreman, workers, material_name,
                    quantity_used, unit, img_path
                ) VALUES (
                    seq_work_logs.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11
                )
            """
            self.cursor.execute(sql, (
                orders_seq, work_date, site_number, site_name,
                task_description, foreman, workers, material_name,
                quantity_used, unit, img_path
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("작업일지 insert 실패:", e)
            return False
        finally:
            self.disconnect()

    def get_all_work_logs(self):
        return self.fetch_all(
            "SELECT * FROM work_logs ORDER BY logs_seq DESC"
        )

    def get_work_log_by_id(self, logs_seq):
        rows = self.fetch_all(
            "SELECT * FROM work_logs WHERE logs_seq = :id",
            {"id": logs_seq}
        )
        return rows[0] if rows else None

    def update_work_log(self, logs_seq, orders_seq, work_date, site_number, site_name,
                        task_description, foreman, workers, material_name,
                        quantity_used, unit, img_path):
        try:
            self.connect()
            sql = """
                UPDATE work_logs SET
                    orders_seq      = :1,
                    work_date       = :2,
                    site_number     = :3,
                    site_name       = :4,
                    task_description= :5,
                    foreman         = :6,
                    workers         = :7,
                    material_name   = :8,
                    quantity_used   = :9,
                    unit            = :10,
                    img_path        = :11
                WHERE logs_seq       = :12
            """
            self.cursor.execute(sql, (
                orders_seq, work_date, site_number, site_name,
                task_description, foreman, workers, material_name,
                quantity_used, unit, img_path, logs_seq
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("작업일지 수정 실패:", e)
            return False
        finally:
            self.disconnect()

    def delete_work_log(self, logs_seq):
        try:
            self.connect()
            self.cursor.execute("DELETE FROM work_logs WHERE logs_seq = :1", (logs_seq,))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("작업일지 삭제 실패:", e)
            return False
        finally:
            self.disconnect()

    # ============================================================
    # 3) vendors CRUD
    # ============================================================
    def get_all_vendors(self):
        return self.fetch_all(
            "SELECT * FROM vendors ORDER BY vendors_seq DESC"
        )

    def get_vendor_by_id(self, vendors_seq):
        rows = self.fetch_all(
            "SELECT * FROM vendors WHERE vendors_seq = :id",
            {"id": vendors_seq}
        )
        return rows[0] if rows else None

    def insert_vendor(self, vendors_name, contact_person, phone, address, email):
        try:
            self.connect()
            sql = """
                INSERT INTO vendors (
                    vendors_seq, vendors_name, contact_person,
                    phone, address, email
                ) VALUES (
                    seq_vendors.NEXTVAL, :1, :2, :3, :4, :5
                )
            """
            self.cursor.execute(sql, (
                vendors_name, contact_person, phone, address, email
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("공급업체 등록 실패:", e)
            return False
        finally:
            self.disconnect()

    def update_vendor(self, vendors_seq, vendors_name, contact_person, phone, address, email):
        try:
            self.connect()
            sql = """
                UPDATE vendors SET
                    vendors_name   = :1,
                    contact_person = :2,
                    phone          = :3,
                    address        = :4,
                    email          = :5
                WHERE vendors_seq  = :6
            """
            self.cursor.execute(sql, (
                vendors_name, contact_person, phone, address, email, vendors_seq
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("공급업체 수정 실패:", e)
            return False
        finally:
            self.disconnect()

    def delete_vendor(self, vendors_seq):
        try:
            self.connect()
            self.cursor.execute(
                "DELETE FROM vendors WHERE vendors_seq = :1", (vendors_seq,)
            )
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("공급업체 삭제 실패:", e)
            return False
        finally:
            self.disconnect()

    # ============================================================
    # 4) material_transactions CRUD
    # ============================================================
    def get_all_material_transactions(self):
        return self.fetch_all(
            "SELECT * FROM material_transactions ORDER BY trans_seq DESC"
        )

    def get_transaction_by_id(self, trans_seq):
        rows = self.fetch_all(
            "SELECT * FROM material_transactions WHERE trans_seq = :id",
            {"id": trans_seq}
        )
        return rows[0] if rows else None

    def insert_material_transaction(self, transaction_date, vendors_seq,
                                    material_name, quantity, unit, price,
                                    orders_seq, img_path):
        try:
            self.connect()
            sql = """
                INSERT INTO material_transactions (
                    trans_seq, transaction_date, vendors_seq, material_name,
                    quantity, unit, price, orders_seq, img_path
                ) VALUES (
                    seq_material_transactions.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8
                )
            """
            self.cursor.execute(sql, (
                transaction_date or datetime.now(), vendors_seq, material_name,
                quantity, unit, price, orders_seq, img_path
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("거래 등록 실패:", e)
            return False
        finally:
            self.disconnect()

    def insert_material_transactions(self, transaction_date, vendors_seq,
                                     orders_seq, materials: list):
        try:
            self.connect()
            sql = """
                INSERT INTO material_transactions (
                    trans_seq, transaction_date, vendors_seq, material_name,
                    quantity, unit, price, orders_seq, img_path
                ) VALUES (
                    seq_material_transactions.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8
                )
            """
            for m in materials:
                self.cursor.execute(sql, (
                    transaction_date or datetime.now(),
                    vendors_seq,
                    m.get('material_name'),
                    m.get('quantity'),
                    m.get('unit'),
                    m.get('price'),
                    orders_seq,
                    m.get('img_path')
                ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("1:N 거래 등록 실패:", e)
            return False
        finally:
            self.disconnect()

    def update_material_transaction(self, trans_seq, transaction_date, vendors_seq,
                                    material_name, quantity, unit, price,
                                    orders_seq, img_path):
        try:
            self.connect()
            sql = """
                UPDATE material_transactions SET
                    transaction_date = :1,
                    vendors_seq      = :2,
                    material_name    = :3,
                    quantity         = :4,
                    unit             = :5,
                    price            = :6,
                    orders_seq       = :7,
                    img_path         = :8
                WHERE trans_seq       = :9
            """
            self.cursor.execute(sql, (
                transaction_date, vendors_seq, material_name, quantity,
                unit, price, orders_seq, img_path, trans_seq
            ))
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("거래 수정 실패:", e)
            return False
        finally:
            self.disconnect()

    def delete_material_transaction(self, trans_seq):
        try:
            self.connect()
            self.cursor.execute(
                "DELETE FROM material_transactions WHERE trans_seq = :1",
                (trans_seq,)
            )
            self.connection.commit()
            return True
        except cx_Oracle.Error as e:
            self.connection.rollback()
            print("거래 삭제 실패:", e)
            return False
        finally:
            self.disconnect()

    # ============================================================
    # 5) 집계 메서드 (대시보드)
    # ============================================================
    def get_progress_data(self):
        sql = """
        SELECT  o.orders_seq                 AS order_id,
                o.contract_name,
                o.process_name,
                o.material_name,
                o.unit,
                o.start_date,
                o.end_date,
                o.planned_quantity,
                NVL(SUM(l.quantity_used), 0) AS used_quantity
        FROM    work_orders o
        LEFT JOIN work_logs l
            ON l.orders_seq     = o.orders_seq
            AND l.material_name  = o.material_name
        GROUP  BY o.orders_seq, o.contract_name, o.process_name,
                o.material_name, o.unit,
                o.start_date, o.end_date, o.planned_quantity
        ORDER  BY o.end_date
        """
        rows  = self.fetch_all(sql)
        today = date.today()                     # 옵션 A: date 객체

        result = []
        for r in rows:
            # 날짜 타입 맞추기 ──────────────────────
            s_date = r["start_date"].date() if isinstance(r["start_date"], datetime) else r["start_date"]
            e_date = r["end_date"].date()   if isinstance(r["end_date"],   datetime) else r["end_date"]

            # 자재 사용률 %
            planned_qty = r["planned_quantity"] or 0
            used_qty    = r["used_quantity"]    or 0
            mat_pct     = round(used_qty / planned_qty * 100, 1) if planned_qty else 0

            # 일정 진행률 %
            total_days   = max((e_date - s_date).days, 1)
            elapsed_days = max((today  - s_date).days, 0)
            time_pct     = round(min(elapsed_days / total_days, 1) * 100, 1)

            # 결과 dict
            result.append({
                **r,
                "material_percent": mat_pct,     # ← 여기서 mat_pct 사용
                "time_percent"    : time_pct,
                "days_left"       : (e_date - today).days
            })
        return result

    def get_inventory_status(self):
        sql = """
        SELECT 
            mt.material_name,
            mt.unit,
            NVL(SUM(mt.quantity),      0) AS total_supplied,
            NVL(SUM(wl.quantity_used), 0) AS total_used,
            NVL(SUM(mt.quantity), 0) - NVL(SUM(wl.quantity_used), 0) AS remaining_quantity
        FROM material_transactions mt
        LEFT JOIN work_logs wl
               ON mt.material_name = wl.material_name
              AND mt.unit          = wl.unit
        GROUP BY mt.material_name, mt.unit
        ORDER BY remaining_quantity DESC
        """
        return self.fetch_all(sql)
