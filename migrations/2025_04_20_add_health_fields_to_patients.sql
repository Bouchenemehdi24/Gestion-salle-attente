-- Migration to add health monitoring fields to patients table
ALTER TABLE patients ADD COLUMN blood_pressure_systolic INTEGER NULL;
ALTER TABLE patients ADD COLUMN blood_pressure_diastolic INTEGER NULL;
ALTER TABLE patients ADD COLUMN oxygen_saturation INTEGER NULL;
ALTER TABLE patients ADD COLUMN heart_rate INTEGER NULL;
