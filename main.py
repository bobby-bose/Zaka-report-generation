from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import json
import sys
import webbrowser
from datetime import datetime
from ZC.logic import prepare_invoice_data

def number_to_words(num):
    """Convert number to words for currency amounts"""
    if not num or num == '0' or num == '0.00':
        return "Zero"
    
    # Convert to float and handle decimal places
    try:
        num_float = float(num)
    except (ValueError, TypeError):
        return "Zero"
    
    # Split into integer and decimal parts
    integer_part = int(num_float)
    decimal_part = round((num_float - integer_part) * 100)
    
    # Words for numbers
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def convert_less_than_thousand(n):
        if n == 0:
            return ''
        elif n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 != 0 else '')
        else:
            return ones[n // 100] + ' Hundred' + (' ' + convert_less_than_thousand(n % 100) if n % 100 != 0 else '')
    
    def convert_integer(n):
        if n == 0:
            return 'Zero'
        result = ''
        
        # Crore (10 million)
        if n >= 10000000:
            result += convert_less_than_thousand(n // 10000000) + ' Crore '
            n %= 10000000
        
        # Lakh (100 thousand)
        if n >= 100000:
            result += convert_less_than_thousand(n // 100000) + ' Lakh '
            n %= 100000
        
        # Thousand
        if n >= 1000:
            result += convert_less_than_thousand(n // 1000) + ' Thousand '
            n %= 1000
        
        # Hundred and below
        if n > 0:
            result += convert_less_than_thousand(n)
        
        return result.strip()
    
    # Convert integer part
    words = convert_integer(integer_part)
    
    # Add decimal part if exists
    if decimal_part > 0:
        words += ' and ' + convert_less_than_thousand(decimal_part) + ' Paise'
    
    return words + ' Rupees'

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)), static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Database Configuration
if getattr(sys, 'frozen', False):
    appdata_dir = os.environ.get('APPDATA') or os.path.expanduser('~')
    db_dir = os.path.join(appdata_dir, 'ReportGeneration')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'web_forms.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web_forms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class PackagingList(db.Model):
    __tablename__ = 'packaging_list'
    id = db.Column(db.Integer, primary_key=True)
    packingListNo = db.Column(db.String(100), nullable=True)
    date = db.Column(db.Date, nullable=True)
    consigneeAddress = db.Column(db.Text, nullable=True)
    deliveryAddress = db.Column(db.Text, nullable=True)
    exporterAddress = db.Column(db.Text, nullable=True)
    poNumber = db.Column(db.String(100), nullable=True)
    loadingPort = db.Column(db.String(100), nullable=True)
    dischargePort = db.Column(db.String(100), nullable=True)
    hsCode = db.Column(db.String(100), nullable=True)
    taxNumber = db.Column(db.String(100), nullable=True)
    
    # New Fields for the Module System
    currency = db.Column(db.String(10), default='USD')
    moduleAType = db.Column(db.String(10)) # A1, A2, or A3
    moduleA_data = db.Column(db.JSON)       # Stores the list or object for Module A
    moduleBType = db.Column(db.String(10)) # B1, B2, or B3
    moduleB_data = db.Column(db.JSON)       # Stores the list or object for Module B
    
    total_net_weight = db.Column(db.Float, default=0.0)
    total_gross_weight = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.now)


class ProformaInvoice(db.Model):
    __tablename__ = 'proforma_invoice'
    id = db.Column(db.Integer, primary_key=True)
    invoice_date = db.Column(db.String(50), nullable=True)
    invoice_no = db.Column(db.String(100), nullable=True)
    po_wo_number = db.Column(db.String(100), nullable=True)
    our_ref_no = db.Column(db.String(100), nullable=True)
    your_reference_no = db.Column(db.String(100), nullable=True)
    supplier_address = db.Column(db.Text, nullable=True)
    bill_to_address = db.Column(db.Text, nullable=True)
    total_amount = db.Column(db.String(50), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    advance_amount = db.Column(db.String(50), nullable=True)
    discount_percentage = db.Column(db.String(50), nullable=True)
    discount_amount = db.Column(db.String(50), nullable=True)
    receivable_amount = db.Column(db.String(50), nullable=True)
    received_amount = db.Column(db.String(100), nullable=True)
    balance_amount = db.Column(db.String(50), nullable=True)
    country_of_origin = db.Column(db.String(100), nullable=True)
    port_of_embarkation = db.Column(db.String(100), nullable=True)
    port_of_discharge = db.Column(db.String(100), nullable=True)
    line_items = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class ZCExporter(db.Model):
    __tablename__ = 'zc_exporter'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), nullable=True)
    invoice_date = db.Column(db.String(50), nullable=True)
    buyer_order_number = db.Column(db.String(100), nullable=True)
    buyer_order_date = db.Column(db.String(50), nullable=True)
    exporter_reference = db.Column(db.String(100), nullable=True)
    iec_number = db.Column(db.String(100), nullable=True)
    tax_registration_number = db.Column(db.String(100), nullable=True)
    lut_arn_number = db.Column(db.String(100), nullable=True)
    delivery_payment_terms = db.Column(db.Text, nullable=True)
    port_of_loading = db.Column(db.String(100), nullable=True)
    port_of_discharge = db.Column(db.String(100), nullable=True)
    pre_carriage_by = db.Column(db.String(100), nullable=True)
    place_of_receipt = db.Column(db.String(100), nullable=True)
    port_of_destination = db.Column(db.String(100), nullable=True)
    destination = db.Column(db.String(100), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    vessel_flight = db.Column(db.String(100), nullable=True)
    country_of_origin = db.Column(db.String(100), nullable=True)
    ad_code = db.Column(db.String(100), nullable=True)
    other_reference = db.Column(db.String(100), nullable=True)
    hs_code = db.Column(db.String(100), nullable=True)
    final_destination = db.Column(db.String(100), nullable=True)
    contact_person_name = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    consignee_address = db.Column(db.Text, nullable=True)
    delivery_address = db.Column(db.Text, nullable=True)
    amount_in_words = db.Column(db.String(200), nullable=True)
    total_export_value = db.Column(db.String(50), nullable=True)
    total_gst_value = db.Column(db.String(50), nullable=True)
    total_invoice_value = db.Column(db.String(50), nullable=True)
    number_of_boxes = db.Column(db.Integer, nullable=True)
    items = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


def _ensure_packaging_list_schema():
    if not (db.engine and db.engine.url and db.engine.url.drivername and db.engine.url.drivername.startswith('sqlite')):
        return

    wanted = {
        'currency': "VARCHAR(10) DEFAULT 'USD'",
        'moduleAType': 'VARCHAR(10)',
        'moduleA_data': 'TEXT',
        'moduleBType': 'VARCHAR(10)',
        'moduleB_data': 'TEXT',
        'total_net_weight': 'REAL DEFAULT 0.0',
        'total_gross_weight': 'REAL DEFAULT 0.0',
        'status': "VARCHAR(20) DEFAULT 'Completed'",
        'created_at': 'DATETIME',
    }

    with db.engine.begin() as conn:
        cols = conn.execute(text('PRAGMA table_info(packaging_list)')).fetchall()
        existing = {row[1] for row in cols}
        for col, ddl in wanted.items():
            if col in existing:
                continue
            conn.execute(text(f'ALTER TABLE packaging_list ADD COLUMN {col} {ddl}'))


def _ensure_proforma_invoice_schema():
    if not (db.engine and db.engine.url and db.engine.url.drivername and db.engine.url.drivername.startswith('sqlite')):
        return

    wanted = {
        'advance_amount': 'VARCHAR(50)',
    }

    with db.engine.begin() as conn:
        cols = conn.execute(text('PRAGMA table_info(proforma_invoice)')).fetchall()
        existing = {row[1] for row in cols}
        for col, ddl in wanted.items():
            if col in existing:
                continue
            conn.execute(text(f'ALTER TABLE proforma_invoice ADD COLUMN {col} {ddl}'))

# Define the folders and their routes
FORMS = {
    'Packaging List': '/packaging_list/view',
    'Proforma Invoice': '/proforma_invoice/view',
    'ZC Exporter': '/zc_exporter/view'
}

@app.route('/')
def home():
    return render_template('main.html', forms=FORMS)

@app.route('/packaging_list')
def packaging_list():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'packaging_list'), 'add.html')

@app.route('/packaging_list/view')
def packaging_list_view():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'packaging_list'), 'view.html')

@app.route('/proforma_invoice')
def proforma_invoice():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'proforma_invoice'), 'add.html')

@app.route('/proforma_invoice/view')
def proforma_invoice_view():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'proforma_invoice'), 'view.html')

@app.route('/zc_exporter')
def zc_exporter():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'ZC'), 'add.html')

@app.route('/ZC/<path:filename>')
def zc_exporter_assets(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'ZC'), filename)

@app.route('/zc_exporter/view')
def zc_exporter_view():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'ZC'), 'view.html')

# Edit Routes with data loaded from database
@app.route('/packaging_list/edit')
def packaging_list_edit():
    record_id = request.args.get('id')
    if record_id:
        record = PackagingList.query.get(record_id)
        if record:
            return render_template('packaging_list/edit.html', record=record)
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'packaging_list'), 'edit.html')

@app.route('/proforma_invoice/edit')
def proforma_invoice_edit():
    record_id = request.args.get('id')
    if record_id:
        record = ProformaInvoice.query.get(record_id)
        if record:
            return render_template('proforma_invoice/edit.html', record=record)
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'proforma_invoice'), 'edit.html')

@app.route('/zc_exporter/edit')
def zc_exporter_edit():
    record_id = request.args.get('id')
    if record_id:
        record = ZCExporter.query.get(record_id)
        if record:
            return render_template('ZC/edit.html', record=record)
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'ZC'), 'edit.html')

@app.route('/packaging_list/print/<int:id>')
def packaging_list_print(id):
    try:
        record = PackagingList.query.get(id)
        if not record:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        
        def _as_dict(v):
            if v is None:
                return {}
            if isinstance(v, dict):
                return v
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return {}
            return {}

        # Prepare data for template
        items_data = []
        moduleB_data = _as_dict(getattr(record, 'moduleB_data', None))

        # Expected shape: { itemHierarchies: [ { itemNumber, associatedBoxes:[{boxNo, description, qty, dimensions, weights}, ...] } ] }
        if isinstance(moduleB_data.get('itemHierarchies'), list):
            for h in moduleB_data.get('itemHierarchies'):
                if not isinstance(h, dict):
                    continue
                item_no = str(h.get('itemNumber', '')).strip()
                for b in h.get('associatedBoxes') or []:
                    if not isinstance(b, dict):
                        continue
                    dims = b.get('dimensions') if isinstance(b.get('dimensions'), dict) else {}
                    wts = b.get('weights') if isinstance(b.get('weights'), dict) else {}
                    items_data.append({
                        'itemNos': item_no,
                        'boxNos': str(b.get('boxNo', '')).strip(),
                        'description': str(b.get('description', '')).strip(),
                        'qty': b.get('qty', ''),
                        'l': dims.get('l', ''),
                        'w': dims.get('w', ''),
                        'h': dims.get('h', ''),
                        'netWt': wts.get('net', ''),
                        'grossWt': wts.get('gross', ''),
                    })
        else:
            legacy_items = getattr(record, 'items', None)
            if isinstance(legacy_items, list):
                items_data = legacy_items
        
        # Calculate totals
        total_net_weight = 0
        total_gross_weight = 0
        total_boxes = 0

        def _safe_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        unique_boxes = set()
        for item in items_data:
            net = item.get('netWt') or item.get('netWeight') or item.get('net_weight', 0)
            gross = item.get('grossWt') or item.get('grossWeight') or item.get('gross_weight', 0)
            total_net_weight += _safe_float(net)
            total_gross_weight += _safe_float(gross)

            box_nos = item.get('boxNos') or ''
            for part in str(box_nos).split(','):
                box = part.strip()
                if box:
                    unique_boxes.add(box)

        total_boxes = len(unique_boxes)

        def _to_int_or_str(val):
            s = str(val).strip()
            if s.isdigit():
                return int(s)
            return s

        sorted_items = sorted(
            items_data,
            key=lambda x: (
                _to_int_or_str(x.get('itemNos', '')),
                _to_int_or_str(x.get('boxNos', '')),
                str(x.get('description', '')).strip(),
            ),
        )

        grouped_items = []
        current = None
        for item in sorted_items:
            item_nos = str(item.get('itemNos', '')).strip()
            desc = str(item.get('description', '')).strip()

            row = {
                'boxNos': str(item.get('boxNos', '')).strip(),
                'description': desc,
                'qty': item.get('qty', ''),
                'l': item.get('l', ''),
                'w': item.get('w', ''),
                'h': item.get('h', ''),
                'netWt': item.get('netWt') or item.get('netWeight') or item.get('net_weight', ''),
                'grossWt': item.get('grossWt') or item.get('grossWeight') or item.get('gross_weight', ''),
            }

            if current and current.get('itemNos') == item_nos:
                current['rows'].append(row)
                current['rowspan'] = len(current['rows'])
            else:
                current = {
                    'itemNos': item_nos,
                    'rows': [row],
                    'rowspan': 1,
                }
                grouped_items.append(current)

        for g in grouped_items:
            descriptions = [str(r.get('description', '')).strip() for r in g.get('rows', [])]
            first_desc = descriptions[0] if descriptions else ''
            g['description_merged'] = bool(descriptions) and all(d == first_desc for d in descriptions)
            g['description'] = first_desc if g['description_merged'] else ''
            g['description_rowspan'] = g['rowspan'] if g['description_merged'] else 1
        
        data = {
            'consigneeAddress': record.consigneeAddress or '',
            'taxNumber': record.taxNumber or '',
            'deliveryAddress': record.deliveryAddress or '',
            'date': record.date.strftime('%Y-%m-%d') if record.date else '',
            'po_no': record.poNumber or '',
            'packing_list_no': record.packingListNo or '',
            'loding_port': record.loadingPort or '',
            'discharge_port': record.dischargePort or '',
            'hs_code': record.hsCode or '',
            'total_boxes': total_boxes,
            'items': grouped_items,
            'total_net_weight': f"{total_net_weight:.2f}",
            'total_gross_weight': f"{total_gross_weight:.2f}"
        }
        
        # Save data to JSON file in packaging_list folder
        packaging_folder = os.path.join(os.path.dirname(__file__), 'packaging_list')
        json_file_path = os.path.join(packaging_folder, 'data.json')
        
        with open(json_file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return render_template('packaging_list/packing_start.html', **data)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/proforma_invoice/print/<int:id>')
def proforma_invoice_print(id):
    try:
        record = ProformaInvoice.query.get(id)
        if not record:
            return jsonify({'success': False, 'message': 'Record not found'}), 404

        def _sf(v):
            try:
                if v is None:
                    return 0.0
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v)
                cleaned = ''.join(ch for ch in s if (ch.isdigit() or ch in '.-'))
                return float(cleaned) if cleaned else 0.0
            except Exception:
                return 0.0

        currency = (record.currency or 'USD').strip()
        currency_u = currency.upper()
        rate = 1.0
        if currency_u == 'USD':
            rate = 90.0
        elif currency_u in ('DINAR', 'DNR', 'KWD'):
            rate = 286.0

        total_in_inr = _sf(record.total_amount)
        advance_in_inr = _sf(record.advance_amount)
        received_in_inr = _sf(record.received_amount)
        balance_in_inr = _sf(record.balance_amount)

        # These are used in the right-side numeric cells.
        total_amount_fmt = f"{total_in_inr:.2f}"
        advance_amount_fmt = f"{advance_in_inr:.2f}"
        received_amount_fmt = f"{received_in_inr:.2f}"
        balance_amount_fmt = f"{balance_in_inr:.2f}"

        # These are used in the left-side spans; convert from INR when currency is USD/DINAR.
        advance_amount_display = f"{(advance_in_inr / rate):.2f}"
        balance_amount_display = f"{(balance_in_inr / rate):.2f}"

        data = {
            'bill_to_address': record.bill_to_address or '',
            'date': record.invoice_date or '',
            'invoice_no': record.invoice_no or '',
            'po_wo_number': record.po_wo_number or '',
            'your_reference_no': record.your_reference_no or '',
            'our_reference_no': record.our_ref_no or '',
            'currency': currency,
            'items': record.line_items or [],

            'total_amount': total_amount_fmt,
            'advance_amount': advance_amount_fmt,
            'received_details': record.receivable_amount or '',
            'received_amount': received_amount_fmt,
            'balance_amount': balance_amount_fmt,

            'advance_amount_display': advance_amount_display,
            'balance_amount_display': balance_amount_display,

            'country_of_origin': record.country_of_origin or '',
            'port_of_embarkation': record.port_of_embarkation or '',
            'port_of_discharge': record.port_of_discharge or '',
            'date_created': record.created_at.strftime('%Y-%m-%d') if record.created_at else ''
        }

        return render_template('proforma_invoice/start.html', **data)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/zc_exporter/print/<int:id>')
def zc_exporter_print(id):
    try:
        record = ZCExporter.query.get(id)
        if not record:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        
        # Use logic module to prepare data with dynamic row calculation
        data = prepare_invoice_data(record)
        
        # Save data to JSON file in ZC folder
        zc_folder = os.path.join(os.path.dirname(__file__), 'ZC')
        json_file_path = os.path.join(zc_folder, 'data.json')
        
        with open(json_file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return render_template('ZC/start.html', **data)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/packaging-list/create', methods=['POST'])
def create_packaging_list():
    try:
        data = request.get_json()
        
        # --- 1. Helper for Float Conversion ---
        def _sf(v):
            try: return float(v) if v else 0.0
            except: return 0.0

        a_type = data.get('moduleAType')
        a_data = data.get('moduleA', {})
        b_type = data.get('moduleBType')
        b_data = data.get('moduleB', [])

        def _normalize_a1_rows(raw_a1):
            # Supports:
            # - Flattened rows: [{boxNumbers, description, qty, l, w, h, netWt, grossWt}, ...]
            # - Nested sections: [{material:{description}, boxes:[{boxNumber,...}, ...]}, ...]
            out = []
            if not isinstance(raw_a1, list):
                return out

            for entry in raw_a1:
                if not isinstance(entry, dict):
                    continue

                is_nested = isinstance(entry.get('boxes'), list) and isinstance(entry.get('material'), dict)
                if is_nested:
                    desc = str((entry.get('material') or {}).get('description') or '')
                    for box in entry.get('boxes') or []:
                        if not isinstance(box, dict):
                            continue
                        out.append({
                            'boxNumbers': box.get('boxNumber') or box.get('boxNumbers') or '',
                            'description': desc,
                            'qty': box.get('qty'),
                            'l': box.get('l'),
                            'w': box.get('w'),
                            'h': box.get('h'),
                            'netWt': box.get('netWt'),
                            'grossWt': box.get('grossWt'),
                        })
                    continue

                # Assume already-flat row (keep a stable shape for downstream)
                out.append({
                    'boxNumbers': entry.get('boxNumbers') or entry.get('boxNumber') or '',
                    'description': entry.get('description') or '',
                    'qty': entry.get('qty'),
                    'l': entry.get('l'),
                    'w': entry.get('w'),
                    'h': entry.get('h'),
                    'netWt': entry.get('netWt'),
                    'grossWt': entry.get('grossWt'),
                })

            return out

        def _parse_tokens(v):
            raw = str(v or '').strip()
            if not raw:
                return []
            out = []
            for token in raw.split(','):
                t = token.strip()
                if not t:
                    continue
                if '-' in t:
                    parts = [p.strip() for p in t.split('-', 1)]
                    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        a = int(parts[0])
                        b = int(parts[1])
                        start = min(a, b)
                        end = max(a, b)
                        out.extend([str(n) for n in range(start, end + 1)])
                        continue
                out.append(t)
            return out

        def _safe_max(a, b):
            try:
                fa = float(a) if a not in (None, '') else None
            except Exception:
                fa = None
            try:
                fb = float(b) if b not in (None, '') else None
            except Exception:
                fb = None
            if fa is None:
                return fb
            if fb is None:
                return fa
            return max(fa, fb)

        def _aggregate_a2_materials(materials):
            descs = []
            qty_sum = 0.0
            net_sum = 0.0
            gross_sum = 0.0
            l_max = None
            w_max = None
            h_max = None
            for m in materials or []:
                d = (m.get('description') or '').strip() if isinstance(m, dict) else ''
                if d:
                    descs.append(d)
                if isinstance(m, dict):
                    qty_sum += _sf(m.get('qty'))
                    net_sum += _sf(m.get('netWt'))
                    gross_sum += _sf(m.get('grossWt'))
                    l_max = _safe_max(l_max, m.get('l'))
                    w_max = _safe_max(w_max, m.get('w'))
                    h_max = _safe_max(h_max, m.get('h'))
            return {
                'description': ' | '.join(descs) if descs else 'N/A',
                'qty': qty_sum,
                'l': l_max,
                'w': w_max,
                'h': h_max,
                'netWt': net_sum,
                'grossWt': gross_sum,
                'materials': materials or []
            }

        # --- 2. Calculate Weights (User Logic) ---
        total_net = 0.0
        total_gross = 0.0

        if a_type == 'A1': # List of multiple box objects
            for r in _normalize_a1_rows(a_data):
                total_net += _sf(r.get('netWt'))
                total_gross += _sf(r.get('grossWt'))
        elif a_type == 'A2': # Nested Materials
            for m in a_data.get('materials', []):
                total_net += _sf(m.get('netWt'))
                total_gross += _sf(m.get('grossWt'))
        elif a_type == 'A3': # Single Box Object
            total_net = _sf(a_data.get('netWt'))
            total_gross = _sf(a_data.get('grossWt'))

        # --- 3. Transformation: Build the Relational JSON ---
        # We pivot on Box Number but group by Item Number (Left Side)
        
        # Step A: Create a lookup for Box Details from Module A
        # (Handling the common A3 single-object case or A1 list case)
        box_lookup = {}
        if a_type == 'A3' and isinstance(a_data, dict):
            for b_no in _parse_tokens(a_data.get('boxNumber')):
                box_lookup[str(b_no)] = a_data
        elif a_type == 'A1' and isinstance(a_data, list):
            for r in _normalize_a1_rows(a_data):
                for b_no in _parse_tokens(r.get('boxNumbers')):
                    box_lookup[str(b_no)] = r
        elif a_type == 'A2' and isinstance(a_data, dict):
            for b_no in _parse_tokens(a_data.get('boxNumber')):
                box_lookup[str(b_no)] = _aggregate_a2_materials(a_data.get('materials', []))

        # Normalize Module B to: item_number -> set(box_numbers)
        item_to_boxes = {}
        if b_type == 'B1' and isinstance(b_data, list):
            for r in b_data:
                if not isinstance(r, dict):
                    continue
                for box_no in _parse_tokens(r.get('boxNumber')):
                    for item_no in _parse_tokens(r.get('itemNumbers')):
                        item_to_boxes.setdefault(str(item_no), set()).add(str(box_no))
        elif b_type == 'B2' and isinstance(b_data, list):
            for r in b_data:
                if not isinstance(r, dict):
                    continue
                for item_no in _parse_tokens(r.get('itemNumber')):
                    for box_no in _parse_tokens(r.get('boxNumbers')):
                        item_to_boxes.setdefault(str(item_no), set()).add(str(box_no))
        elif b_type == 'B3' and isinstance(b_data, dict):
            for item_no in _parse_tokens(b_data.get('itemNumber')):
                for box_no in _parse_tokens(b_data.get('boxNumber')):
                    item_to_boxes.setdefault(str(item_no), set()).add(str(box_no))

        # Determine box -> items, for Many-to-One detection
        box_to_items = {}
        for item_no, boxes in item_to_boxes.items():
            for b_no in boxes:
                box_to_items.setdefault(b_no, set()).add(item_no)

        # Step B: Build Item Hierarchies (The "Left Side" logic)
        item_hierarchies = []
        def _sort_key(x):
            return int(x) if str(x).isdigit() else str(x)

        for item_no in sorted(item_to_boxes.keys(), key=_sort_key):
            box_list = sorted(list(item_to_boxes.get(item_no, set())), key=_sort_key)

            # Determine Relationship Type
            rel_type = "One-to-One"
            if any(len(box_to_items.get(b_no, set())) > 1 for b_no in box_list):
                rel_type = "Many-to-One"
            elif len(box_list) > 1:
                rel_type = "One-to-Many"

            # Map details from the "Right Side" (Module A)
            associated_boxes = []
            for b_no in box_list:
                details = box_lookup.get(b_no, {})
                associated_boxes.append({
                    "boxNo": b_no,
                    "description": details.get('description', 'N/A') if isinstance(details, dict) else 'N/A',
                    "qty": _sf(details.get('qty')) if isinstance(details, dict) else 0.0,
                    "dimensions": {
                        "l": details.get('l') if isinstance(details, dict) else None,
                        "w": details.get('w') if isinstance(details, dict) else None,
                        "h": details.get('h') if isinstance(details, dict) else None
                    },
                    "weights": {
                        "net": _sf(details.get('netWt')) if isinstance(details, dict) else 0.0,
                        "gross": _sf(details.get('grossWt')) if isinstance(details, dict) else 0.0
                    }
                })

            item_hierarchies.append({
                "itemNumber": item_no,
                "relationship": rel_type,
                "associatedBoxes": associated_boxes
            })

        # --- 4. Final Structured Data Object ---
        # This reflects the format you requested for the JSON output and DB storage
        final_relational_data = {
            "itemHierarchies": item_hierarchies,
            "summary": {
                "total_net": total_net,
                "total_gross": total_gross,
                "currency": data.get('currency', 'USD')
            }
        }

        # --- 5. Save to Database ---
        packaging = PackagingList(
            packingListNo=data.get('packingListNo'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else None,
            consigneeAddress=data.get('consigneeAddress'),
            deliveryAddress=data.get('deliveryAddress'),
            exporterAddress=data.get('exporterAddress'),
            poNumber=data.get('poNumber'),
            loadingPort=data.get('loadingPort'),
            dischargePort=data.get('dischargePort'),
            hsCode=data.get('hsCode'),
            taxNumber=data.get('taxNumber'),
            currency=data.get('currency'),
            moduleAType=a_type,
            moduleA_data=a_data,          # Original raw box data
            moduleBType=data.get('moduleBType'),
            moduleB_data=final_relational_data, # STORE THE NEW STRUCTURED RELATIONSHIP HERE
            total_net_weight=total_net,
            total_gross_weight=total_gross
        )
        db.session.add(packaging)
        db.session.commit()

        # --- 6. Create .json file ---
        filename = f"packing_list_{data.get('packingListNo') or 'temp'}.json"
        file_path = os.path.join(os.getcwd(), filename)
        
        with open(file_path, 'w') as f:
            # We dump the relational data to the file as well
            json.dump(final_relational_data, f, indent=4)

        return jsonify({
            'success': True, 
            'message': f'Saved to DB and created {filename}', 
            'data': final_relational_data, # Return the relational format
            'id': packaging.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/packaging-list/<int:id>/update', methods=['PUT'])
def update_packaging_list(id):
    try:
        data = request.get_json()
        packaging = PackagingList.query.get(id)
        
        if not packaging:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        
        # Update fields
        packaging.packingListNo = data.get('packingListNo', packaging.packingListNo)
        if data.get('date'):
            packaging.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        packaging.consigneeAddress = data.get('consigneeAddress', packaging.consigneeAddress)
        packaging.deliveryAddress = data.get('deliveryAddress', packaging.deliveryAddress)
        packaging.exporterAddress = data.get('exporterAddress', packaging.exporterAddress)
        packaging.poNumber = data.get('poNumber', packaging.poNumber)
        packaging.loadingPort = data.get('loadingPort', packaging.loadingPort)
        packaging.dischargePort = data.get('dischargePort', packaging.dischargePort)
        packaging.hsCode = data.get('hsCode', packaging.hsCode)
        packaging.taxNumber = data.get('taxNumber', packaging.taxNumber)
        packaging.items = data.get('items', packaging.items)
        
        # Recalculate totals
        items_data = packaging.items or []
        total_net_weight = 0
        total_gross_weight = 0

        def _safe_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        for item in items_data:
            net = item.get('netWt') or item.get('netWeight') or item.get('net_weight', 0)
            gross = item.get('grossWt') or item.get('grossWeight') or item.get('gross_weight', 0)
            total_net_weight += _safe_float(net)
            total_gross_weight += _safe_float(gross)
        
        packaging.total_net_weight = total_net_weight
        packaging.total_gross_weight = total_gross_weight
        packaging.updated_at = datetime.now()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Packaging list updated successfully', 'id': packaging.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/proforma-invoice/create', methods=['POST'])
def create_proforma_invoice():
    try:
        data = request.get_json()

        def _sf(v):
            try:
                if v is None:
                    return 0.0
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v)
                cleaned = ''.join(ch for ch in s if (ch.isdigit() or ch in '.-'))
                return float(cleaned) if cleaned else 0.0
            except Exception:
                return 0.0

        currency = (data.get('currency') or 'INR').strip().upper()

        # Conversion divisor (from INR to selected currency)
        divisor = 1.0
        if currency == 'USD':
            divisor = 90.0
        elif currency in ('DINAR', 'DNR', 'KWD'):
            divisor = 286.0

        # Values entered (assumed INR reference)
        total_inr = _sf(data.get('totalAmount'))
        advance_inr = _sf(data.get('advanceAmount'))
        received_inr = _sf(data.get('receivedAmount'))

        # Convert line items BEFORE storing (assumed INR reference)
        line_items_final = []
        raw_items = data.get('lineItems') or []
        if isinstance(raw_items, list):
            for it in raw_items:
                if not isinstance(it, dict):
                    continue
                qty = _sf(it.get('quantity'))
                unit_inr = _sf(it.get('unitRate'))
                total_line_inr = _sf(it.get('total'))

                unit_final = round(unit_inr / divisor, 2)
                if total_line_inr:
                    total_final_line = round(total_line_inr / divisor, 2)
                else:
                    total_final_line = round(qty * unit_final, 2)

                line_items_final.append({
                    'lineNo': it.get('lineNo'),
                    'partNumber': it.get('partNumber') or '',
                    'description': it.get('description') or '',
                    'quantity': str(it.get('quantity') or ''),
                    'unitRate': f"{unit_final:.2f}",
                    'total': f"{total_final_line:.2f}",
                })

        # Convert BEFORE storing
        total_final = round(total_inr / divisor, 2)
        advance_final = round(advance_inr / divisor, 2)
        received_final = round(received_inr / divisor, 2)

        receivable_final = round(total_final - advance_final, 2)
        balance_final = round(receivable_final - received_final, 2)



        invoice = ProformaInvoice(
            invoice_date=data.get('invoiceDate'),
            invoice_no=data.get('invoiceNo'),
            po_wo_number=data.get('poWoNumber'),
            our_ref_no=data.get('yourRefNo'),
            your_reference_no=data.get('yourReferenceNo'),
            supplier_address=data.get('supplierAddress'),
            bill_to_address=data.get('billToAddress'),

            currency=currency,

            total_amount=total_final,
            advance_amount=advance_final,
            receivable_amount=receivable_final,
            received_amount=received_final,
            balance_amount=balance_final,

            country_of_origin=data.get('countryOfOrigin'),
            port_of_embarkation=data.get('portOfEmbarkation'),
            port_of_discharge=data.get('portOfDischarge'),
            line_items=line_items_final
        )

        # show the invoice in a json format
        # total_amount=total_final,
        #     advance_amount=advance_final,
        #     receivable_amount=receivable_final,
        #     received_amount=received_final,
        #     balance_amount=balance_final,
        print({
            'total_amount': total_final,
            'advance_amount': advance_final,
            'receivable_amount': receivable_final,
            'received_amount': received_final,
            'balance_amount': balance_final
        })

        db.session.add(invoice)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Proforma invoice created successfully',
            'id': invoice.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400



@app.route('/api/proforma-invoice/<int:id>/update', methods=['PUT'])
def update_proforma_invoice(id):
    try:
        data = request.get_json()
        invoice = ProformaInvoice.query.get(id)
        
        if not invoice:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        
        def _sf(v):
            try:
                if v is None:
                    return 0.0
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v)
                cleaned = ''.join(ch for ch in s if (ch.isdigit() or ch in '.-'))
                return float(cleaned) if cleaned else 0.0
            except Exception:
                return 0.0

        currency = (data.get('currency') or invoice.currency or 'INR').strip().upper()
        divisor = 1.0
        if currency == 'USD':
            divisor = 90.0
        elif currency in ('DINAR', 'DNR', 'KWD'):
            divisor = 286.0

        total_inr = _sf(data.get('totalAmount'))
        advance_inr = _sf(data.get('advanceAmount'))
        received_inr = _sf(data.get('receivedAmount'))

        total_final = round(total_inr / divisor, 2)
        advance_final = round(advance_inr / divisor, 2)
        received_final = round(received_inr / divisor, 2)

        receivable_final = round(total_final - advance_final, 2)
        balance_final = round(receivable_final - received_final, 2)

        line_items_final = []
        raw_items = data.get('lineItems') or []
        if isinstance(raw_items, list):
            for it in raw_items:
                if not isinstance(it, dict):
                    continue
                qty = _sf(it.get('quantity'))
                unit_inr = _sf(it.get('unitRate'))
                total_line_inr = _sf(it.get('total'))

                unit_final = round(unit_inr / divisor, 2)
                if total_line_inr:
                    total_final_line = round(total_line_inr / divisor, 2)
                else:
                    total_final_line = round(qty * unit_final, 2)

                line_items_final.append({
                    'lineNo': it.get('lineNo'),
                    'partNumber': it.get('partNumber') or '',
                    'description': it.get('description') or '',
                    'quantity': str(it.get('quantity') or ''),
                    'unitRate': f"{unit_final:.2f}",
                    'total': f"{total_final_line:.2f}",
                })

        # Update fields
        invoice.invoice_date = data.get('invoiceDate', invoice.invoice_date)
        invoice.invoice_no = data.get('invoiceNo', invoice.invoice_no)
        invoice.po_wo_number = data.get('poWoNumber', invoice.po_wo_number)
        invoice.our_ref_no = data.get('yourRefNo', invoice.our_ref_no)
        invoice.your_reference_no = data.get('yourReferenceNo', invoice.your_reference_no)
        invoice.supplier_address = data.get('supplierAddress', invoice.supplier_address)
        invoice.bill_to_address = data.get('billToAddress', invoice.bill_to_address)

        invoice.currency = currency
        invoice.total_amount = total_final
        invoice.advance_amount = advance_final
        invoice.receivable_amount = receivable_final
        invoice.received_amount = received_final
        invoice.balance_amount = balance_final

        invoice.country_of_origin = data.get('countryOfOrigin', invoice.country_of_origin)
        invoice.port_of_embarkation = data.get('portOfEmbarkation', invoice.port_of_embarkation)
        invoice.port_of_discharge = data.get('portOfDischarge', invoice.port_of_discharge)
        invoice.line_items = line_items_final
        invoice.updated_at = datetime.now()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Proforma invoice updated successfully', 'id': invoice.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/zc-exporter/create', methods=['POST'])
def create_zc_exporter():
    try:
        data = request.get_json()
        
        # Create new ZC exporter entry
        exporter = ZCExporter(
            invoice_number=data.get('invoiceNumber'),
            invoice_date=data.get('invoiceDate'),
            buyer_order_number=data.get('buyerOrderNumber'),
            buyer_order_date=data.get('buyerOrderDate'),
            exporter_reference=data.get('exporterReference'),
            iec_number=data.get('iecNumber'),
            tax_registration_number=data.get('taxRegistrationNumber'),
            lut_arn_number=data.get('lutArnNumber'),
            delivery_payment_terms=data.get('deliveryPaymentTerms'),
            port_of_loading=data.get('portOfLoading'),
            port_of_discharge=data.get('portOfDischarge'),
            pre_carriage_by=data.get('preCarriageBy'),
            place_of_receipt=data.get('placeOfReceipt'),
            port_of_destination=data.get('portOfDestination'),
            destination=data.get('destination'),
            currency=data.get('currency'),
            vessel_flight=data.get('vesselFlight'),
            country_of_origin=data.get('countryOfOrigin'),
            ad_code=data.get('adCode'),
            other_reference=data.get('otherReference'),
            hs_code=data.get('hsCode'),
            final_destination=data.get('finalDestination'),
            contact_person_name=data.get('contactPersonName'),
            contact_email=data.get('contactEmail'),
            consignee_address=data.get('consigneeAddress'),
            delivery_address=data.get('deliveryAddress'),
            amount_in_words=data.get('amountInWords'),
            total_export_value=data.get('totalExportValue'),
            total_gst_value=data.get('totalGstValue'),
            total_invoice_value=data.get('totalInvoiceValue'),
            number_of_boxes=data.get('numberOfBoxes'),
            items=data.get('items')
        )
        
        db.session.add(exporter)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'ZC exporter created successfully', 'id': exporter.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/zc-exporter/<int:id>/update', methods=['PUT'])
def update_zc_exporter(id):
    try:
        data = request.get_json()
        exporter = ZCExporter.query.get(id)
        
        if not exporter:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        
        # Update fields
        exporter.invoice_number = data.get('invoiceNumber', exporter.invoice_number)
        exporter.invoice_date = data.get('invoiceDate', exporter.invoice_date)
        exporter.buyer_order_number = data.get('buyerOrderNumber', exporter.buyer_order_number)
        exporter.buyer_order_date = data.get('buyerOrderDate', exporter.buyer_order_date)
        exporter.exporter_reference = data.get('exporterReference', exporter.exporter_reference)
        exporter.iec_number = data.get('iecNumber', exporter.iec_number)
        exporter.tax_registration_number = data.get('taxRegistrationNumber', exporter.tax_registration_number)
        exporter.lut_arn_number = data.get('lutArnNumber', exporter.lut_arn_number)
        exporter.delivery_payment_terms = data.get('deliveryPaymentTerms', exporter.delivery_payment_terms)
        exporter.port_of_loading = data.get('portOfLoading', exporter.port_of_loading)
        exporter.port_of_discharge = data.get('portOfDischarge', exporter.port_of_discharge)
        exporter.pre_carriage_by = data.get('preCarriageBy', exporter.pre_carriage_by)
        exporter.place_of_receipt = data.get('placeOfReceipt', exporter.place_of_receipt)
        exporter.port_of_destination = data.get('portOfDestination', exporter.port_of_destination)
        exporter.destination = data.get('destination', exporter.destination)
        exporter.currency = data.get('currency', exporter.currency)
        exporter.vessel_flight = data.get('vesselFlight', exporter.vessel_flight)
        exporter.country_of_origin = data.get('countryOfOrigin', exporter.country_of_origin)
        exporter.ad_code = data.get('adCode', exporter.ad_code)
        exporter.other_reference = data.get('otherReference', exporter.other_reference)
        exporter.hs_code = data.get('hsCode', exporter.hs_code)
        exporter.final_destination = data.get('finalDestination', exporter.final_destination)
        exporter.contact_person_name = data.get('contactPersonName', exporter.contact_person_name)
        exporter.contact_email = data.get('contactEmail', exporter.contact_email)
        exporter.consignee_address = data.get('consigneeAddress', exporter.consignee_address)
        exporter.delivery_address = data.get('deliveryAddress', exporter.delivery_address)
        exporter.amount_in_words = data.get('amountInWords', exporter.amount_in_words)
        exporter.total_export_value = data.get('totalExportValue', exporter.total_export_value)
        exporter.total_gst_value = data.get('totalGstValue', exporter.total_gst_value)
        exporter.total_invoice_value = data.get('totalInvoiceValue', exporter.total_invoice_value)
        exporter.number_of_boxes = data.get('numberOfBoxes', exporter.number_of_boxes)
        exporter.items = data.get('items', exporter.items)
        exporter.updated_at = datetime.now()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'ZC exporter updated successfully', 'id': exporter.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# API Routes to fetch data
@app.route('/api/packaging-list', methods=['GET'])
def get_packaging_lists():
    try:
        # Return records ordered strictly by id desc (latest created first)
        items = PackagingList.query.order_by(PackagingList.id.desc()).all()
        return jsonify([{
            'id': item.id,
            'packingListNo': item.packingListNo or '',
            'poNumber': item.poNumber or '',
            'consigneeAddress': item.consigneeAddress or '',
            'status': item.status or 'Completed',
            'createdAt': item.created_at.strftime('%Y-%m-%d') if item.created_at else '',
            # PackagingList currently does not have updated_at; keep key for UI compatibility
            'updatedAt': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else ''
        } for item in items]), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/packaging-list/<int:id>', methods=['GET'])
def get_packaging_list(id):
    try:
        item = PackagingList.query.get(id)
        if not item:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        return jsonify({
            'id': item.id,
            'packingListNo': item.packingListNo,
            'date': item.date.strftime('%Y-%m-%d') if item.date else '',
            'consigneeAddress': item.consigneeAddress,
            'deliveryAddress': item.deliveryAddress,
            'exporterAddress': item.exporterAddress,
            'poNumber': item.poNumber,
            'loadingPort': item.loadingPort,
            'dischargePort': item.dischargePort,
            'hsCode': item.hsCode,
            'taxNumber': item.taxNumber,
            'items': item.items,
            'status': item.status,
            'createdAt': item.created_at.strftime('%Y-%m-%d') if item.created_at else ''
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/proforma-invoice', methods=['GET'])
def get_proforma_invoices():
    try:
        # Return records ordered strictly by id desc (latest created first)
        items = ProformaInvoice.query.order_by(ProformaInvoice.id.desc()).all()
        return jsonify([{
            'id': item.id,
            'invoiceNo': item.invoice_no or '',
            'poWoNumber': item.po_wo_number or '',
            'billToAddress': item.bill_to_address or '',
            'totalAmount': item.total_amount or '',
            'currency': item.currency or 'USD',
            'status': item.status or 'Completed',
            'createdAt': item.created_at.strftime('%Y-%m-%d') if item.created_at else '',
            'updatedAt': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        } for item in items]), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/proforma-invoice/<int:id>', methods=['GET'])
def get_proforma_invoice(id):
    try:
        item = ProformaInvoice.query.get(id)
        if not item:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        return jsonify({
            'id': item.id,
            'invoiceDate': item.invoice_date,
            'invoiceNo': item.invoice_no,
            'poWoNumber': item.po_wo_number,
            'yourRefNo': item.our_ref_no,
            'yourReferenceNo': item.your_reference_no,
            'supplierAddress': item.supplier_address,
            'billToAddress': item.bill_to_address,
            'totalAmount': item.total_amount,
            'currency': item.currency,
            'advanceAmount': item.advance_amount,
            'receivableAmount': item.receivable_amount,
            'receivedAmount': item.received_amount,
            'balanceAmount': item.balance_amount,
            'countryOfOrigin': item.country_of_origin,
            'portOfEmbarkation': item.port_of_embarkation,
            'portOfDischarge': item.port_of_discharge,
            'lineItems': item.line_items,
            'status': item.status,
            'createdAt': item.created_at.strftime('%Y-%m-%d') if item.created_at else ''
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/zc-exporter', methods=['GET'])
def get_zc_exporters():
    try:
        # Return records ordered strictly by id desc (latest created first)
        items = ZCExporter.query.order_by(ZCExporter.id.desc()).all()
        return jsonify([{
            'id': item.id,
            'invoiceNumber': item.invoice_number or '',
            'invoiceDate': item.invoice_date or '',
            'exporterReference': item.exporter_reference or '',
            'consigneeAddress': item.consignee_address or '',
            'totalInvoiceValue': item.total_invoice_value or '',
            'status': item.status,
            'createdAt': item.created_at.strftime('%Y-%m-%d') if item.created_at else '',
            'updatedAt': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        } for item in items]), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/zc-exporter/<int:id>', methods=['GET'])
def get_zc_exporter(id):
    try:
        item = ZCExporter.query.get(id)
        if not item:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        return jsonify({
            'id': item.id,
            'invoiceNumber': item.invoice_number,
            'invoiceDate': item.invoice_date,
            'buyerOrderNumber': item.buyer_order_number,
            'buyerOrderDate': item.buyer_order_date,
            'exporterReference': item.exporter_reference,
            'iecNumber': item.iec_number,
            'taxRegistrationNumber': item.tax_registration_number,
            'lutArnNumber': item.lut_arn_number,
            'deliveryPaymentTerms': item.delivery_payment_terms,
            'portOfLoading': item.port_of_loading,
            'portOfDischarge': item.port_of_discharge,
            'preCarriageBy': item.pre_carriage_by,
            'placeOfReceipt': item.place_of_receipt,
            'portOfDestination': item.port_of_destination,
            'destination': item.destination,
            'currency': item.currency,
            'vesselFlight': item.vessel_flight,
            'countryOfOrigin': item.country_of_origin,
            'adCode': item.ad_code,
            'otherReference': item.other_reference,
            'hsCode': item.hs_code,
            'finalDestination': item.final_destination,
            'contactPersonName': item.contact_person_name,
            'contactEmail': item.contact_email,
            'consigneeAddress': item.consignee_address,
            'deliveryAddress': item.delivery_address,
            'amountInWords': item.amount_in_words,
            'totalExportValue': item.total_export_value,
            'totalGstValue': item.total_gst_value,
            'totalInvoiceValue': item.total_invoice_value,
            'numberOfBoxes': item.number_of_boxes,
            'items': item.items,
            'status': item.status,
            'createdAt': item.created_at.strftime('%Y-%m-%d') if item.created_at else ''
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        _ensure_packaging_list_schema()
        _ensure_proforma_invoice_schema()
    
  

    
    # Run the Flask app
    app.run(debug=True, port=5000)
