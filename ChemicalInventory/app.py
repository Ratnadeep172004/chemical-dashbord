import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///chemical_inventory.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models and routes
    import models  # noqa: F401
    import routes  # noqa: F401
    
    # Create all tables
    db.create_all()
    
    # Initialize sample data if tables are empty
    from models import ChemicalMaster
    if ChemicalMaster.query.count() == 0:
        logging.info("Initializing sample chemical master data...")
        sample_chemicals = [
            ChemicalMaster(
                unit_code="PROCESS_UNITS",
                unit_name="Process Units",
                chemical_code="C01",
                chemical_name="Demineralized Water",
                sap_material_code="10001",
                unit="KG",
                stock_in_sap=1000.0,
                avg_daily_consumption=50.0,
                status="Active"
            ),
            ChemicalMaster(
                unit_code="PROCESS_UNITS", 
                unit_name="Process Units",
                chemical_code="C02",
                chemical_name="Corrosion Inhibitor",
                sap_material_code="10002",
                unit="KG", 
                stock_in_sap=500.0,
                avg_daily_consumption=25.0,
                status="Active"
            ),
            ChemicalMaster(
                unit_code="PROCESS_UNITS",
                unit_name="Process Units", 
                chemical_code="C03",
                chemical_name="Hydrazine",
                sap_material_code="10003",
                unit="KG",
                stock_in_sap=200.0,
                avg_daily_consumption=10.0,
                status="Active"
            ),
            ChemicalMaster(
                unit_code="UTILITY_UNITS",
                unit_name="Utility Units",
                chemical_code="C04", 
                chemical_name="Sodium Hypochlorite",
                sap_material_code="10004",
                unit="LITER",
                stock_in_sap=800.0,
                avg_daily_consumption=40.0,
                status="Active"
            ),
            ChemicalMaster(
                unit_code="UTILITY_UNITS",
                unit_name="Utility Units",
                chemical_code="C05",
                chemical_name="Ferric Chloride",
                sap_material_code="10005", 
                unit="KG",
                stock_in_sap=300.0,
                avg_daily_consumption=15.0,
                status="Active"
            )
        ]
        
        for chemical in sample_chemicals:
            db.session.add(chemical)
        
        try:
            db.session.commit()
            logging.info("Sample chemical master data created successfully")
        except Exception as e:
            logging.error(f"Error creating sample data: {e}")
            db.session.rollback()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
