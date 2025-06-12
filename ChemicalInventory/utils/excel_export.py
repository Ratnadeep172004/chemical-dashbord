import pandas as pd
from io import BytesIO
from datetime import datetime
import logging

def generate_excel_report(consumption_records):
    """
    Generate Excel report from consumption records
    
    Args:
        consumption_records: List of DailyConsumption model instances
        
    Returns:
        BytesIO: Excel file in memory
    """
    try:
        # Convert records to list of dictionaries
        data = []
        for record in consumption_records:
            data.append({
                'Date': record.dc_date.strftime('%Y-%m-%d') if record.dc_date else '',
                'Unit Code': record.unit_code,
                'Unit Name': record.unit_name,
                'Chemical Code': record.chemical_code,
                'Chemical Name': record.chemical_name,
                'SAP Material Code': record.sap_code,
                'UOM': get_uom_from_chemical_master(record.unit_code, record.chemical_code),
                'Opening Balance': float(record.opening_balance) if record.opening_balance else 0.0,
                'Receive Qty': float(record.receive_qty) if record.receive_qty else 0.0,
                'Consumption Qty': float(record.consumption_qty) if record.consumption_qty else 0.0,
                'Closing Balance': float(record.closing_balance) if record.closing_balance else 0.0,
                'SAP Balance': float(record.sap_balance) if record.sap_balance else 0.0,
                'Remarks': record.remarks or '',
                'User ID': record.user_id,
                'Data Insert Date': record.data_insert_date.strftime('%Y-%m-%d %H:%M:%S') if record.data_insert_date else '',
                'Status': record.status
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data sheet
            df.to_excel(writer, sheet_name='Consumption Report', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Consumption Report']
            
            # Format headers
            header_font = workbook.create_style(
                name='header',
                font=workbook.fonts['Arial'],
                fill=workbook.colors['blue'],
                alignment=workbook.alignments['center']
            ) if hasattr(workbook, 'create_style') else None
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Add summary sheet
            create_summary_sheet(writer, df)
        
        output.seek(0)
        return output
        
    except Exception as e:
        logging.error(f"Error generating Excel report: {e}")
        raise

def get_uom_from_chemical_master(unit_code, chemical_code):
    """Get UOM from chemical master table"""
    try:
        from models import ChemicalMaster
        chemical = ChemicalMaster.query.filter_by(
            unit_code=unit_code,
            chemical_code=chemical_code
        ).first()
        return chemical.unit if chemical else 'N/A'
    except Exception as e:
        logging.error(f"Error getting UOM: {e}")
        return 'N/A'

def create_summary_sheet(writer, df):
    """Create a summary sheet with aggregated data"""
    try:
        # Create summary data
        summary_data = []
        
        # Group by chemical and calculate totals
        chemical_summary = df.groupby(['Chemical Name']).agg({
            'Opening Balance': 'last',
            'Receive Qty': 'sum',
            'Consumption Qty': 'sum',
            'Closing Balance': 'last'
        }).reset_index()
        
        # Add summary info
        summary_info = {
            'Report Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Total Records': len(df),
            'Date Range': f"{df['Date'].min()} to {df['Date'].max()}" if len(df) > 0 else 'No data',
            'Total Chemicals': df['Chemical Name'].nunique() if len(df) > 0 else 0,
            'Total Units': df['Unit Name'].nunique() if len(df) > 0 else 0
        }
        
        # Create summary DataFrame
        summary_df = pd.DataFrame([summary_info])
        
        # Write summary sheet
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        chemical_summary.to_excel(writer, sheet_name='Chemical Summary', index=False)
        
        # Format summary sheets
        for sheet_name in ['Summary', 'Chemical Summary']:
            if sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
    except Exception as e:
        logging.error(f"Error creating summary sheet: {e}")
