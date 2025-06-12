import logging
from datetime import datetime, date
from flask import render_template, request, jsonify, send_file, session, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from app import app, db
from models import ChemicalMaster, DailyConsumption
from utils.excel_export import generate_excel_report
from utils.calculations import calculate_closing_balance

def login_required(f):
    """Decorator to require login for protected routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        
        # Simple authentication
        if user_id == 'admin001' and password == 'admin001':
            session['logged_in'] = True
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main page route"""
    return render_template('index.html')

@app.route('/api/units', methods=['GET'])
@login_required
def get_units():
    """Get all unique units"""
    try:
        units = db.session.query(ChemicalMaster.unit_code, ChemicalMaster.unit_name).distinct().all()
        unit_list = [{'code': unit.unit_code, 'name': unit.unit_name} for unit in units]
        return jsonify({'success': True, 'units': unit_list})
    except Exception as e:
        logging.error(f"Error fetching units: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chemicals/<unit_code>', methods=['GET'])
@login_required
def get_chemicals_by_unit(unit_code):
    """Get chemicals for a specific unit"""
    try:
        chemicals = ChemicalMaster.query.filter_by(unit_code=unit_code, status='Active').all()
        chemical_list = [chem.to_dict() for chem in chemicals]
        return jsonify({'success': True, 'chemicals': chemical_list})
    except Exception as e:
        logging.error(f"Error fetching chemicals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chemical_details/<unit_code>/<chemical_code>', methods=['GET'])
@login_required
def get_chemical_details(unit_code, chemical_code):
    """Get chemical details and last consumption data"""
    try:
        # Get chemical master data
        chemical = ChemicalMaster.query.filter_by(
            unit_code=unit_code, 
            chemical_code=chemical_code,
            status='Active'
        ).first()
        
        if not chemical:
            return jsonify({'success': False, 'error': 'Chemical not found'}), 404
        
        # Get last consumption record for opening balance
        last_consumption = DailyConsumption.query.filter_by(
            unit_code=unit_code,
            chemical_code=chemical_code
        ).order_by(DailyConsumption.dc_date.desc()).first()
        
        opening_balance = last_consumption.closing_balance if last_consumption else 0.0
        
        response_data = {
            'chemical_details': chemical.to_dict(),
            'opening_balance': float(opening_balance),
            'last_consumption_date': last_consumption.dc_date.strftime('%Y-%m-%d') if last_consumption else None
        }
        
        return jsonify({'success': True, 'data': response_data})
    except Exception as e:
        logging.error(f"Error fetching chemical details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/submit_consumption', methods=['POST'])
@login_required
def submit_consumption():
    """Submit daily consumption data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['dc_date', 'unit_code', 'chemical_code', 'opening_balance', 'receive_qty', 'consumption_qty']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Parse and validate date
        try:
            consumption_date = datetime.strptime(data['dc_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Prevent future dates
        if consumption_date > date.today():
            return jsonify({'success': False, 'error': 'Cannot enter data for future dates'}), 400
        
        # Get chemical master data
        chemical = ChemicalMaster.query.filter_by(
            unit_code=data['unit_code'],
            chemical_code=data['chemical_code'],
            status='Active'
        ).first()
        
        if not chemical:
            return jsonify({'success': False, 'error': 'Chemical not found in master data'}), 404
        
        # Calculate closing balance
        opening_balance = float(data['opening_balance'])
        receive_qty = float(data.get('receive_qty', 0))
        consumption_qty = float(data.get('consumption_qty', 0))
        closing_balance = calculate_closing_balance(opening_balance, receive_qty, consumption_qty)
        
        # Check if record already exists
        existing_record = DailyConsumption.query.filter_by(
            dc_date=consumption_date,
            unit_code=data['unit_code'],
            chemical_code=data['chemical_code']
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.opening_balance = opening_balance
            existing_record.receive_qty = receive_qty
            existing_record.consumption_qty = consumption_qty
            existing_record.closing_balance = closing_balance
            existing_record.sap_balance = float(data.get('sap_balance', 0))
            existing_record.remarks = data.get('remarks', '')
            existing_record.update_date = datetime.now()
            existing_record.user_id = data.get('user_id', 'system')
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Consumption data updated successfully', 'data': existing_record.to_dict()})
        
        else:
            # Create new record
            new_consumption = DailyConsumption(
                dc_date=consumption_date,
                unit_code=data['unit_code'],
                chemical_code=data['chemical_code'],
                unit_name=chemical.unit_name,
                chemical_name=chemical.chemical_name,
                sap_code=chemical.sap_material_code,
                opening_balance=opening_balance,
                receive_qty=receive_qty,
                consumption_qty=consumption_qty,
                closing_balance=closing_balance,
                sap_balance=float(data.get('sap_balance', 0)),
                remarks=data.get('remarks', ''),
                user_id=data.get('user_id', 'system')
            )
            
            db.session.add(new_consumption)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Consumption data saved successfully', 'data': new_consumption.to_dict()})
    
    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Database integrity error: {e}")
        return jsonify({'success': False, 'error': 'Data integrity error. Record may already exist.'}), 400
    
    except ValueError as e:
        logging.error(f"Value error in consumption submission: {e}")
        return jsonify({'success': False, 'error': 'Invalid numeric values provided'}), 400
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error submitting consumption: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/consumption_data', methods=['GET'])
@login_required
def get_consumption_data():
    """Get consumption data with optional filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        unit_code = request.args.get('unit_code')
        chemical_code = request.args.get('chemical_code')
        
        # Build query
        query = DailyConsumption.query
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(DailyConsumption.dc_date >= start_date_obj)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(DailyConsumption.dc_date <= end_date_obj)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        if unit_code:
            query = query.filter(DailyConsumption.unit_code == unit_code)
        
        if chemical_code:
            query = query.filter(DailyConsumption.chemical_code == chemical_code)
        
        # Execute query
        consumption_records = query.order_by(DailyConsumption.dc_date.desc()).all()
        
        # Convert to dict
        data = [record.to_dict() for record in consumption_records]
        
        return jsonify({'success': True, 'data': data, 'count': len(data)})
    
    except Exception as e:
        logging.error(f"Error fetching consumption data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export_excel', methods=['GET'])
@login_required
def export_excel():
    """Export consumption data to Excel"""
    try:
        # Get query parameters (same as consumption_data endpoint)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        unit_code = request.args.get('unit_code')
        chemical_code = request.args.get('chemical_code')
        
        # Build query
        query = DailyConsumption.query
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(DailyConsumption.dc_date >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(DailyConsumption.dc_date <= end_date_obj)
        
        if unit_code:
            query = query.filter(DailyConsumption.unit_code == unit_code)
        
        if chemical_code:
            query = query.filter(DailyConsumption.chemical_code == chemical_code)
        
        # Get data
        consumption_records = query.order_by(DailyConsumption.dc_date.desc()).all()
        
        if not consumption_records:
            return jsonify({'success': False, 'error': 'No data found for the specified criteria'}), 404
        
        # Generate Excel file
        excel_file = generate_excel_report(consumption_records)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f'chemical_consumption_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logging.error(f"Error exporting to Excel: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
