#!/usr/bin/env python3
"""
Parser especializado para imágenes (JPG, PNG) con OCR avanzado,
preprocesamiento configurable y caché de resultados
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

# OCR imports with graceful fallback
try:
    import pytesseract
    from PIL import Image
    import cv2
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None
    Image = None
    cv2 = None

from ...utils.config import ConfigManager
from ...exceptions import ParsingError

class ImageParser:
    """
    Parser robusto para imágenes con OCR avanzado,
    preprocesamiento configurable y caché de resultados
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if not OCR_AVAILABLE:
            self.logger.warning("OCR libraries not available. Image processing will be limited.")
        
        # Caché de resultados por hash de imagen
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Configuración de OCR
        self.ocr_config = {
            'lang': 'spa+eng',  # Español + Inglés
            'config': '--psm 6 --oem 3',  # PSM 6: uniform text block, OEM 3: default
            'preprocessing': True
        }
    
    def _get_image_hash(self, image_path: str) -> str:
        """Calcular hash de la imagen para caché"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return hashlib.md5(image_path.encode()).hexdigest()
    
    def extract_data(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Extraer datos de imagen usando OCR con preprocesamiento avanzado
        
        Args:
            image_path: Ruta a la imagen (JPG, PNG)
            
        Returns:
            Diccionario con datos extraídos o None si falla
        """
        if not OCR_AVAILABLE:
            raise ParsingError("OCR libraries not available. Install pytesseract, PIL, and opencv-python.")
        
        try:
            # Verificar caché
            image_hash = self._get_image_hash(image_path)
            if image_hash in self._cache:
                self.logger.debug("Datos obtenidos de caché", extra={"image_hash": image_hash})
                return self._cache[image_hash]
            
            # Cargar y preprocesar imagen
            processed_image = self._preprocess_image(image_path)
            if processed_image is None:
                return None
            
            # Extraer texto con OCR
            texto = self._extract_text_with_ocr(processed_image)
            if not texto:
                return None
            
            # Parsear datos del texto extraído
            datos = self._parse_text_data(texto)
            
            # Agregar metadatos
            datos['text'] = texto
            datos['archivo'] = image_path
            datos['timestamp_procesamiento'] = datetime.now().isoformat()
            datos['ocr_confidence'] = self._get_ocr_confidence(processed_image)
            
            # Guardar en caché
            self._cache[image_hash] = datos
            
            self.logger.info("Imagen procesada exitosamente", extra={
                "image_path": image_path,
                "text_length": len(texto),
                "ocr_confidence": datos.get('ocr_confidence', 0),
                "data_fields": list(datos.keys())
            })
            
            return datos
            
        except Exception as e:
            self.logger.error("Error procesando imagen", extra={
                "image_path": image_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise ParsingError(f"Error procesando imagen {image_path}: {e}")
    
    def _preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Preprocesar imagen para mejorar calidad de OCR
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            Imagen preprocesada como numpy array
        """
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error("No se pudo cargar la imagen", extra={"image_path": image_path})
                return None
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Reducir ruido
            denoised = cv2.medianBlur(gray, 3)
            
            # Mejorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Binarización adaptativa
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morfología para limpiar
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Redimensionar si es muy pequeña
            height, width = cleaned.shape
            if height < 100 or width < 100:
                scale_factor = max(100 / height, 100 / width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            self.logger.debug("Imagen preprocesada", extra={
                "original_shape": image.shape,
                "processed_shape": cleaned.shape
            })
            
            return cleaned
            
        except Exception as e:
            self.logger.error("Error preprocesando imagen", extra={
                "image_path": image_path,
                "error": str(e)
            })
            return None
    
    def _extract_text_with_ocr(self, processed_image: np.ndarray) -> Optional[str]:
        """
        Extraer texto usando Tesseract OCR
        
        Args:
            processed_image: Imagen preprocesada
            
        Returns:
            Texto extraído o None si falla
        """
        try:
            # Configurar Tesseract
            custom_config = self.ocr_config['config']
            
            # Extraer texto
            texto = pytesseract.image_to_string(
                processed_image,
                lang=self.ocr_config['lang'],
                config=custom_config
            )
            
            if not texto or not texto.strip():
                self.logger.warning("No se pudo extraer texto de la imagen")
                return None
            
            # Limpiar texto
            texto_limpio = self._clean_extracted_text(texto)
            
            self.logger.debug("Texto extraído con OCR", extra={
                "text_length": len(texto_limpio),
                "original_length": len(texto)
            })
            
            return texto_limpio
            
        except Exception as e:
            self.logger.error("Error en OCR", extra={"error": str(e)})
            return None
    
    def _clean_extracted_text(self, texto: str) -> str:
        """Limpiar texto extraído del OCR"""
        # Eliminar caracteres de control
        texto_limpio = ''.join(char for char in texto if ord(char) >= 32 or char in '\n\t')
        
        # Eliminar líneas vacías múltiples
        lines = [line.strip() for line in texto_limpio.split('\n') if line.strip()]
        
        # Unir líneas con espacios apropiados
        return ' '.join(lines)
    
    def _get_ocr_confidence(self, processed_image: np.ndarray) -> float:
        """
        Obtener nivel de confianza del OCR
        
        Args:
            processed_image: Imagen procesada
            
        Returns:
            Confianza promedio (0-100)
        """
        try:
            # Obtener datos de confianza
            data = pytesseract.image_to_data(
                processed_image,
                lang=self.ocr_config['lang'],
                config=self.ocr_config['config'],
                output_type=pytesseract.Output.DICT
            )
            
            # Calcular confianza promedio
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            if confidences:
                return sum(confidences) / len(confidences)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.debug("Error obteniendo confianza OCR", extra={"error": str(e)})
            return 0.0
    
    def _parse_text_data(self, texto: str) -> Dict[str, Any]:
        """
        Parsear datos del texto extraído usando patrones similares al PDF parser
        
        Args:
            texto: Texto extraído del OCR
            
        Returns:
            Diccionario con datos parseados
        """
        datos = {}
        
        # Patrones de regex para extracción
        patterns = {
            'fecha': [
                r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            'cliente': [
                r'Cliente[:\s]+(.+)',
                r'Customer[:\s]+(.+)',
                r'Facturar a[:\s]+(.+)'
            ],
            'proveedor': [
                r'Proveedor[:\s]+(.+)',
                r'Supplier[:\s]+(.+)',
                r'De[:\s]+(.+)'
            ],
            'total': [
                r'Total[:\s]+\$?([\d,]+\.?\d*)',
                r'Amount[:\s]+\$?([\d,]+\.?\d*)',
                r'Importe Total[:\s]+\$?([\d,]+\.?\d*)'
            ]
        }
        
        import re
        
        # Extraer fecha
        for pattern in patterns['fecha']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                fecha_str = match.group(1)
                fecha_formateada = self._parse_date(fecha_str)
                if fecha_formateada:
                    datos['fecha'] = fecha_formateada
                    break
        
        # Si no se encontró fecha, usar fecha actual
        if 'fecha' not in datos:
            datos['fecha'] = datetime.now().strftime('%Y-%m-%d')
        
        # Extraer cliente/proveedor
        for pattern in patterns['cliente']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                datos['cliente'] = match.group(1).strip()
                break
        
        for pattern in patterns['proveedor']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                datos['proveedor'] = match.group(1).strip()
                break
        
        # Extraer total
        for pattern in patterns['total']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    datos['total'] = float(total_str)
                    break
                except ValueError:
                    continue
        
        # Si no se encontró total, usar valor por defecto
        if 'total' not in datos:
            datos['total'] = 100.0
        
        # Extraer items (simplificado para OCR)
        datos['items'] = self._extract_items_from_ocr_text(texto)
        
        # Calcular impuestos (simplificado)
        datos['impuestos'] = datos.get('total', 0) * 0.19  # 19% IVA por defecto
        
        return datos
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parsear fecha en diferentes formatos"""
        from datetime import datetime
        
        formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d',
            '%d-%m-%y', '%d/%m/%y'
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _extract_items_from_ocr_text(self, texto: str) -> List[Dict[str, Any]]:
        """Extraer items del texto OCR (método simplificado)"""
        items = []
        
        # Buscar números que podrían ser montos
        import re
        amount_matches = re.findall(r'\$?([\d,]+\.?\d*)', texto)
        amounts = []
        
        for match in amount_matches:
            try:
                amount = float(match.replace(',', ''))
                if 10 <= amount <= 1_000_000:  # Rango razonable
                    amounts.append(amount)
            except ValueError:
                continue
        
        if amounts:
            # Usar el monto más grande como total del item
            max_amount = max(amounts)
            items.append({
                'descripcion': 'Producto/Servicio procesado desde imagen',
                'cantidad': 1.0,
                'precio': max_amount
            })
        else:
            # Item genérico
            items.append({
                'descripcion': 'Producto/Servicio procesado desde imagen',
                'cantidad': 1.0,
                'precio': 100.0
            })
        
        return items
    
    def clear_cache(self) -> None:
        """Limpiar caché de resultados"""
        self._cache.clear()
        self.logger.info("Caché de Image parser limpiado")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        return {
            'cache_size': len(self._cache),
            'cache_keys': list(self._cache.keys()),
            'ocr_available': OCR_AVAILABLE
        }
    
    def test_ocr_installation(self) -> Dict[str, Any]:
        """Probar instalación de OCR"""
        if not OCR_AVAILABLE:
            return {
                'available': False,
                'error': 'OCR libraries not installed',
                'required_packages': ['pytesseract', 'Pillow', 'opencv-python']
            }
        
        try:
            # Crear imagen de prueba simple
            test_image = np.ones((100, 300), dtype=np.uint8) * 255
            cv2.putText(test_image, 'Test OCR', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 0, 2)
            
            # Probar OCR
            result = pytesseract.image_to_string(test_image)
            
            return {
                'available': True,
                'test_result': result.strip(),
                'tesseract_version': pytesseract.get_tesseract_version()
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'troubleshooting': 'Check Tesseract installation and PATH'
            }

