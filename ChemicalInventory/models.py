from app import db
from datetime import datetime
from sqlalchemy import func

class ChemicalMaster(db.Model):
    __tablename__ = 'chemical_master'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_code = db.Column(db.String(100), nullable=False)
    unit_name = db.Column(db.String(100), nullable=False)
    chemical_code = db.Column(db.String(50), nullable=False)
    chemical_name = db.Column(db.String(150), nullable=False)
    sap_material_code = db.Column(db.String(20), nullable=False)
    unit = db.Column(db.String(10), nullable=False)  # UOM
    stock_in_sap = db.Column(db.Numeric(10, 2), default=0.0)
    avg_daily_consumption = db.Column(db.Numeric(10, 2), default=0.0)
    status = db.Column(db.String(20), default='Active')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('unit_code', 'chemical_code', name='uk_unit_chemical'),
    )
    
    def __repr__(self):
        return f'<ChemicalMaster {self.chemical_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'unit_code': self.unit_code,
            'unit_name': self.unit_name,
            'chemical_code': self.chemical_code,
            'chemical_name': self.chemical_name,
            'sap_material_code': self.sap_material_code,
            'unit': self.unit,
            'stock_in_sap': float(self.stock_in_sap) if self.stock_in_sap else 0.0,
            'avg_daily_consumption': float(self.avg_daily_consumption) if self.avg_daily_consumption else 0.0,
            'status': self.status
        }

class DailyConsumption(db.Model):
    __tablename__ = 'daily_consumption'
    
    id = db.Column(db.Integer, primary_key=True)
    dc_date = db.Column(db.Date, nullable=False)
    unit_code = db.Column(db.String(100), nullable=False)
    chemical_code = db.Column(db.String(50), nullable=False)
    unit_name = db.Column(db.String(100), nullable=False)
    chemical_name = db.Column(db.String(150), nullable=False)
    sap_code = db.Column(db.String(20), nullable=False)
    opening_balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    receive_qty = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    consumption_qty = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    closing_balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    sap_balance = db.Column(db.Numeric(10, 2), default=0.0)
    remarks = db.Column(db.String(200))
    user_id = db.Column(db.String(50), default='system')
    data_insert_date = db.Column(db.DateTime, default=func.now())
    update_status = db.Column(db.String(20), default='Active')
    update_date = db.Column(db.DateTime, default=func.now())
    status = db.Column(db.String(20), default='Active')
    
    # Composite unique constraint to prevent duplicate entries for same date, unit, and chemical
    __table_args__ = (
        db.UniqueConstraint('dc_date', 'unit_code', 'chemical_code', name='uk_daily_consumption'),
    )
    
    def __repr__(self):
        return f'<DailyConsumption {self.dc_date} - {self.chemical_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'dc_date': self.dc_date.strftime('%Y-%m-%d') if self.dc_date else None,
            'unit_code': self.unit_code,
            'chemical_code': self.chemical_code,
            'unit_name': self.unit_name,
            'chemical_name': self.chemical_name,
            'sap_code': self.sap_code,
            'opening_balance': float(self.opening_balance) if self.opening_balance else 0.0,
            'receive_qty': float(self.receive_qty) if self.receive_qty else 0.0,
            'consumption_qty': float(self.consumption_qty) if self.consumption_qty else 0.0,
            'closing_balance': float(self.closing_balance) if self.closing_balance else 0.0,
            'sap_balance': float(self.sap_balance) if self.sap_balance else 0.0,
            'remarks': self.remarks,
            'user_id': self.user_id,
            'data_insert_date': self.data_insert_date.strftime('%Y-%m-%d %H:%M:%S') if self.data_insert_date else None,
            'update_status': self.update_status,
            'update_date': self.update_date.strftime('%Y-%m-%d %H:%M:%S') if self.update_date else None,
            'status': self.status
        }
