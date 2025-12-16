from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json
import webbrowser
from datetime import datetime
from ZC.logic import prepare_invoice_data

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)), static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web_forms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class PackagingList(db.Model):
    __tablename__ = 'packaging_list'
    id = db.Column(db.Integer, primary_key=True)
    packingListNo = db.Column('packingListNo', db.String(100), nullable=True)
    date = db.Column('date', db.Date, nullable=True)
    consigneeAddress = db.Column('consigneeAddress', db.Text, nullable=True)
    deliveryAddress = db.Column('deliveryAddress', db.Text, nullable=True)
    exporterAddress = db.Column('exporterAddress', db.Text, nullable=True)
    poNumber = db.Column('poNumber', db.String(100), nullable=True)
    loadingPort = db.Column('loadingPort', db.String(100), nullable=True)
    dischargePort = db.Column('dischargePort', db.String(100), nullable=True)
    hsCode = db.Column('hsCode', db.String(100), nullable=True)
    taxNumber = db.Column('taxNumber', db.String(100), nullable=True)
    items = db.Column('items', db.JSON, nullable=True)
    total_net_weight = db.Column('total_net_weight', db.Float, nullable=True)
    total_gross_weight = db.Column('total_gross_weight', db.Float, nullable=True)
    status = db.Column('status', db.String(20), default='Completed')
    created_at = db.Column('created_at', db.DateTime, default=datetime.now)
    updated_at = db.Column('updated_at', db.DateTime, default=datetime.now, onupdate=datetime.now)

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
        
        # Prepare data for template
        items_data = record.items if record.items else []
        
        # Calculate totals
        total_net_weight = 0
        total_gross_weight = 0
        total_boxes = 0
        
        for item in items_data:
            if 'boxes' in item:
                total_boxes += len(item['boxes'])
                for box in item['boxes']:
                    # Try both camelCase and snake_case for compatibility
                    net = box.get('netWeight') or box.get('net_weight', 0)
                    gross = box.get('grossWeight') or box.get('gross_weight', 0)
                    total_net_weight += float(net) if net else 0
                    total_gross_weight += float(gross) if gross else 0
        
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
            'items': items_data,
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
        
        # Prepare line items
        items_data = record.line_items if record.line_items else []
        
        # Create data dictionary
        data = {
            'bill_to_address': record.bill_to_address or '',
            'date': record.invoice_date or '',
            'invoice_no': record.invoice_no or '',
            'po_wo_number': record.po_wo_number or '',
            'your_reference_no': record.your_reference_no or '',
            'our_reference_no': record.our_ref_no or '',
            'currency': record.currency or 'USD',
            'items': items_data,
            'total_amount': record.total_amount or '0.00',
            'discount_percent': record.discount_percentage or '0',
            'discount_amount': record.discount_amount or '0.00',
            'received_details': record.receivable_amount or '',
            'received_amount': record.received_amount or '0.00',
            'balance_amount': record.balance_amount or '0.00',
            'country_of_origin': record.country_of_origin or '',
            'port_of_embarkation': record.port_of_embarkation or '',
            'port_of_discharge': record.port_of_discharge or '',
            'date_created': record.created_at.strftime('%Y-%m-%d') if record.created_at else ''
        }
        
        # Save to JSON file in proforma_invoice folder
        proforma_folder = os.path.join(os.path.dirname(__file__), 'proforma_invoice')
        json_file_path = os.path.join(proforma_folder, 'data.json')
        
        with open(json_file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
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

# API Routes for Form Submissions
@app.route('/api/packaging-list/create', methods=['POST'])
def create_packaging_list():
    try:
        data = request.get_json()
        
        # Calculate totals from items
        items_data = data.get('items', [])
        total_net_weight = 0
        total_gross_weight = 0
        
        for item in items_data:
            if 'boxes' in item:
                for box in item['boxes']:
                    # Try both camelCase and snake_case for compatibility
                    net = box.get('netWeight') or box.get('net_weight', 0)
                    gross = box.get('grossWeight') or box.get('gross_weight', 0)
                    total_net_weight += float(net) if net else 0
                    total_gross_weight += float(gross) if gross else 0
        
        # Create new packaging list entry
        packaging = PackagingList(
            packingListNo=data.get('packingListNo'),
            date=datetime.strptime(data.get('date', ''), '%Y-%m-%d').date() if data.get('date') else None,
            consigneeAddress=data.get('consigneeAddress'),
            deliveryAddress=data.get('deliveryAddress'),
            exporterAddress=data.get('exporterAddress'),
            poNumber=data.get('poNumber'),
            loadingPort=data.get('loadingPort'),
            dischargePort=data.get('dischargePort'),
            hsCode=data.get('hsCode'),
            taxNumber=data.get('taxNumber'),
            items=items_data,
            total_net_weight=total_net_weight,
            total_gross_weight=total_gross_weight
        )
        
        db.session.add(packaging)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Packaging list created successfully', 'id': packaging.id}), 201
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
        
        for item in items_data:
            if 'boxes' in item:
                for box in item['boxes']:
                    # Try both camelCase and snake_case for compatibility
                    net = box.get('netWeight') or box.get('net_weight', 0)
                    gross = box.get('grossWeight') or box.get('gross_weight', 0)
                    total_net_weight += float(net) if net else 0
                    total_gross_weight += float(gross) if gross else 0
        
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
        
        # Create new proforma invoice entry
        invoice = ProformaInvoice(
            invoice_date=data.get('invoiceDate'),
            invoice_no=data.get('invoiceNo'),
            po_wo_number=data.get('poWoNumber'),
            our_ref_no=data.get('yourRefNo'),
            your_reference_no=data.get('yourReferenceNo'),
            supplier_address=data.get('supplierAddress'),
            bill_to_address=data.get('billToAddress'),
            total_amount=data.get('totalAmount'),
            currency=data.get('currency'),
            discount_percentage=data.get('discountPercentage'),
            discount_amount=data.get('discountAmount'),
            receivable_amount=data.get('receivableAmount'),
            received_amount=data.get('receivedAmount'),
            balance_amount=data.get('balanceAmount'),
            country_of_origin=data.get('countryOfOrigin'),
            port_of_embarkation=data.get('portOfEmbarkation'),
            port_of_discharge=data.get('portOfDischarge'),
            line_items=data.get('lineItems')
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Proforma invoice created successfully', 'id': invoice.id}), 201
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
        
        # Update fields
        invoice.invoice_date = data.get('invoiceDate', invoice.invoice_date)
        invoice.invoice_no = data.get('invoiceNo', invoice.invoice_no)
        invoice.po_wo_number = data.get('poWoNumber', invoice.po_wo_number)
        invoice.our_ref_no = data.get('yourRefNo', invoice.our_ref_no)
        invoice.your_reference_no = data.get('yourReferenceNo', invoice.your_reference_no)
        invoice.supplier_address = data.get('supplierAddress', invoice.supplier_address)
        invoice.bill_to_address = data.get('billToAddress', invoice.bill_to_address)
        invoice.total_amount = data.get('totalAmount', invoice.total_amount)
        invoice.currency = data.get('currency', invoice.currency)
        invoice.discount_percentage = data.get('discountPercentage', invoice.discount_percentage)
        invoice.discount_amount = data.get('discountAmount', invoice.discount_amount)
        invoice.receivable_amount = data.get('receivableAmount', invoice.receivable_amount)
        invoice.received_amount = data.get('receivedAmount', invoice.received_amount)
        invoice.balance_amount = data.get('balanceAmount', invoice.balance_amount)
        invoice.country_of_origin = data.get('countryOfOrigin', invoice.country_of_origin)
        invoice.port_of_embarkation = data.get('portOfEmbarkation', invoice.port_of_embarkation)
        invoice.port_of_discharge = data.get('portOfDischarge', invoice.port_of_discharge)
        invoice.line_items = data.get('lineItems', invoice.line_items)
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
        # Return records ordered by updated_at desc, then created_at desc, then id desc
        items = PackagingList.query.order_by(PackagingList.updated_at.desc(), PackagingList.created_at.desc(), PackagingList.id.desc()).all()
        return jsonify([{
            'id': item.id,
            'packingListNo': item.packingListNo or '',
            'poNumber': item.poNumber or '',
            'consigneeAddress': item.consigneeAddress or '',
            'status': item.status,
            'createdAt': item.created_at.strftime('%Y-%m-%d') if item.created_at else '',
            'updatedAt': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
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
        # Return records ordered by updated_at desc, then created_at desc, then id desc
        items = ProformaInvoice.query.order_by(ProformaInvoice.updated_at.desc(), ProformaInvoice.created_at.desc(), ProformaInvoice.id.desc()).all()
        return jsonify([{
            'id': item.id,
            'invoiceNo': item.invoice_no or '',
            'poWoNumber': item.po_wo_number or '',
            'billToAddress': item.bill_to_address or '',
            'totalAmount': item.total_amount or '',
            'status': item.status,
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
            'discountPercentage': item.discount_percentage,
            'discountAmount': item.discount_amount,
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
        # Return records ordered by id desc, then created_at desc
        items = ZCExporter.query.order_by(ZCExporter.id.desc(), ZCExporter.created_at.desc()).all()
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
    
  

    
    # Run the Flask app
    app.run(debug=True, port=5000)
