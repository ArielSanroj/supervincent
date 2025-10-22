#!/usr/bin/env python3
"""
Supplier database and validation system for Colombian invoices
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class Supplier:
    """Supplier information structure"""
    id: int
    name: str
    normalized_name: str
    phone: str
    bank_account: str
    email: str
    address: str
    tax_id: str
    created_at: datetime
    last_used: datetime
    confidence_score: float

class SupplierDatabase:
    """
    Database for managing and validating supplier information
    """
    
    def __init__(self, db_path: str = "data/suppliers.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize the supplier database"""
        try:
            # Create directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create suppliers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    phone TEXT,
                    bank_account TEXT,
                    email TEXT,
                    address TEXT,
                    tax_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence_score REAL DEFAULT 0.0
                )
            ''')
            
            # Create index for faster searches
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_normalized_name 
                ON suppliers(normalized_name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_phone 
                ON suppliers(phone)
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Supplier database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing supplier database: {e}")
    
    def normalize_name(self, name: str) -> str:
        """Normalize supplier name for better matching"""
        if not name:
            return ""
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', name.strip())
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            'PROVEEDOR', 'SUPPLIER', 'VENDEDOR', 'SEÑOR', 'SR', 'SRA',
            'DOCTOR', 'DR', 'DOCTORA', 'DRA', 'INGENIERO', 'ING', 'INGENIERA'
        ]
        
        for prefix in prefixes_to_remove:
            if normalized.upper().startswith(prefix + ' '):
                normalized = normalized[len(prefix):].strip()
        
        # Remove common suffixes
        suffixes_to_remove = [
            'S.A.S', 'S.A', 'LTDA', 'E.U', 'E.S.P', 'SOCIEDAD',
            'EMPRESA', 'COMPAÑIA', 'COMPANY'
        ]
        
        for suffix in suffixes_to_remove:
            if normalized.upper().endswith(' ' + suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Convert to uppercase for comparison
        return normalized.upper()
    
    def add_supplier(self, name: str, phone: str = "", bank_account: str = "", 
                    email: str = "", address: str = "", tax_id: str = "") -> int:
        """Add a new supplier to the database"""
        try:
            normalized_name = self.normalize_name(name)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if supplier already exists
            cursor.execute('''
                SELECT id FROM suppliers 
                WHERE normalized_name = ? OR phone = ?
            ''', (normalized_name, phone))
            
            existing = cursor.fetchone()
            if existing:
                # Update last_used timestamp
                cursor.execute('''
                    UPDATE suppliers 
                    SET last_used = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (existing[0],))
                conn.commit()
                conn.close()
                return existing[0]
            
            # Insert new supplier
            cursor.execute('''
                INSERT INTO suppliers 
                (name, normalized_name, phone, bank_account, email, address, tax_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, normalized_name, phone, bank_account, email, address, tax_id))
            
            supplier_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added new supplier: {name} (ID: {supplier_id})")
            return supplier_id
            
        except Exception as e:
            self.logger.error(f"Error adding supplier: {e}")
            return -1
    
    def find_supplier(self, name: str, phone: str = "") -> Optional[Supplier]:
        """Find supplier by name or phone"""
        try:
            normalized_name = self.normalize_name(name)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search by normalized name first
            cursor.execute('''
                SELECT * FROM suppliers 
                WHERE normalized_name = ? OR phone = ?
                ORDER BY confidence_score DESC, last_used DESC
                LIMIT 1
            ''', (normalized_name, phone))
            
            row = cursor.fetchone()
            if row:
                conn.close()
                return self._row_to_supplier(row)
            
            # Fuzzy search if exact match not found
            cursor.execute('''
                SELECT * FROM suppliers 
                WHERE normalized_name LIKE ? OR name LIKE ?
                ORDER BY confidence_score DESC, last_used DESC
                LIMIT 1
            ''', (f"%{normalized_name}%", f"%{name}%"))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_supplier(row)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding supplier: {e}")
            return None
    
    def validate_supplier(self, extracted_name: str, extracted_phone: str = "") -> Tuple[bool, str, float]:
        """
        Validate and correct supplier information
        
        Returns:
            (is_valid, corrected_name, confidence_score)
        """
        try:
            # Try to find existing supplier
            supplier = self.find_supplier(extracted_name, extracted_phone)
            
            if supplier:
                # Update last_used
                self._update_last_used(supplier.id)
                return True, supplier.name, supplier.confidence_score
            
            # If not found, try to correct common OCR errors
            corrected_name = self._correct_ocr_errors(extracted_name)
            
            # Check if corrected name exists
            supplier = self.find_supplier(corrected_name, extracted_phone)
            if supplier:
                self._update_last_used(supplier.id)
                return True, supplier.name, supplier.confidence_score * 0.8  # Lower confidence for corrected
            
            # New supplier - add to database
            supplier_id = self.add_supplier(corrected_name, extracted_phone)
            if supplier_id > 0:
                return True, corrected_name, 0.6  # Medium confidence for new supplier
            
            return False, extracted_name, 0.0
            
        except Exception as e:
            self.logger.error(f"Error validating supplier: {e}")
            return False, extracted_name, 0.0
    
    def _correct_ocr_errors(self, name: str) -> str:
        """Correct common OCR errors in supplier names"""
        if not name:
            return name
        
        corrections = {
            # Common OCR character substitutions
            '0': 'O',  # Zero to O
            '1': 'I',  # One to I
            '5': 'S',  # Five to S
            '8': 'B',  # Eight to B
            '6': 'G',  # Six to G
            '3': 'E',  # Three to E
            '4': 'A',  # Four to A
            '7': 'T',  # Seven to T
            '9': 'P',  # Nine to P
            '2': 'Z',  # Two to Z
        }
        
        corrected = name
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)
        
        # Remove common OCR artifacts
        artifacts = ['_', '>', '<', '|', '~', '=', '+', '*', ':', ';']
        for artifact in artifacts:
            corrected = corrected.replace(artifact, ' ')
        
        # Clean up multiple spaces
        corrected = re.sub(r'\s+', ' ', corrected).strip()
        
        return corrected
    
    def _update_last_used(self, supplier_id: int):
        """Update last_used timestamp for supplier"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE suppliers 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (supplier_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error updating last_used: {e}")
    
    def _row_to_supplier(self, row: Tuple) -> Supplier:
        """Convert database row to Supplier object"""
        return Supplier(
            id=row[0],
            name=row[1],
            normalized_name=row[2],
            phone=row[3] or "",
            bank_account=row[4] or "",
            email=row[5] or "",
            address=row[6] or "",
            tax_id=row[7] or "",
            created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
            last_used=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
            confidence_score=row[10] or 0.0
        )
    
    def get_all_suppliers(self) -> List[Supplier]:
        """Get all suppliers from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM suppliers 
                ORDER BY last_used DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_supplier(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting all suppliers: {e}")
            return []
    
    def update_supplier_confidence(self, supplier_id: int, confidence_score: float):
        """Update confidence score for supplier"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE suppliers 
                SET confidence_score = ? 
                WHERE id = ?
            ''', (confidence_score, supplier_id))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error updating confidence: {e}")

# Example usage
if __name__ == "__main__":
    db = SupplierDatabase()
    
    # Add some test suppliers
    db.add_supplier("Juan Hernando Bejarano", "3112062261", "3112062261")
    db.add_supplier("VEGA RODRIGUEZ MARIA CLEMENCIA", "3108824736")
    
    # Test validation
    is_valid, corrected_name, confidence = db.validate_supplier("JUAN HERNANDO BEJARANO", "3112062261")
    print(f"Valid: {is_valid}, Name: {corrected_name}, Confidence: {confidence}")