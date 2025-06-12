-- Create the chemical master table
CREATE TABLE IF NOT EXISTS chemical_master (
    id SERIAL PRIMARY KEY,
    unit_code VARCHAR(100) NOT NULL,
    unit_name VARCHAR(100) NOT NULL,
    chemical_code VARCHAR(50) NOT NULL,
    chemical_name VARCHAR(150) NOT NULL,
    sap_material_code VARCHAR(20) NOT NULL,
    unit VARCHAR(10) NOT NULL,
    stock_in_sap NUMERIC(10, 2),
    avg_daily_consumption NUMERIC(10, 2),
    status VARCHAR(20),
    CONSTRAINT uk_unit_chemical UNIQUE (unit_code, chemical_code),
    CONSTRAINT chemical_master_pkey PRIMARY KEY (id)
);

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS chemical_master_pkey ON chemical_master (id);
CREATE UNIQUE INDEX IF NOT EXISTS uk_unit_chemical ON chemical_master (unit_code, chemical_code);

-- Add comments to columns
COMMENT ON COLUMN chemical_master.id IS 'Primary key';
COMMENT ON COLUMN chemical_master.unit_code IS 'Unique code for the unit';
COMMENT ON COLUMN chemical_master.unit_name IS 'Name of the unit';
COMMENT ON COLUMN chemical_master.chemical_code IS 'Unique code for the chemical';
COMMENT ON COLUMN chemical_master.chemical_name IS 'Name of the chemical';
COMMENT ON COLUMN chemical_master.sap_material_code IS 'SAP material code';
COMMENT ON COLUMN chemical_master.unit IS 'Unit of measurement';
COMMENT ON COLUMN chemical_master.stock_in_sap IS 'Current stock in SAP';
COMMENT ON COLUMN chemical_master.avg_daily_consumption IS 'Average daily consumption';
COMMENT ON COLUMN chemical_master.status IS 'Current status of the inventory';