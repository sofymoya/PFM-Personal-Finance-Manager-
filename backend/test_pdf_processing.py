import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import json
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar las funciones desde el módulo correcto
from app.main import (
    process_bank_statement_pdf, 
    categorize_transaction_openai, 
    detect_bank,
    extract_standard_transactions
)
from app.auth import extract_transactions_with_ai
from app.routers import extract_text_with_ocr


class TestPDFProcessing:
    """Pruebas unitarias para el procesamiento de PDFs"""

    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.sample_pdf_text = """
        BBVA MEXICO
        ESTADO DE CUENTA
        Fecha de operación: 04-Jun-2025
        SU PAGO GRACIAS SPEI A CTA CLABE XXXXXXXX1179 + $9,153.00
        COMPRA TARJETA OXXO MONTERREY - $150.00
        RETIRO CAJERO AUTOMATICO - $500.00
        """

    def test_process_bank_statement_pdf_identifies_bbva(self):
        """Prueba que se identifique correctamente el banco BBVA"""
        with patch('pdfplumber.open') as mock_pdf:
            # Configurar el mock para simular la extracción de texto
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = "BBVA MEXICO ESTADO DE CUENTA"
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert result["banco"] == "BBVA"
                assert "transacciones" in result
                assert "texto_extraido" in result

    def test_process_bank_statement_pdf_identifies_santander(self):
        """Prueba que se identifique correctamente el banco Santander"""
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = "Santander México Estado de Cuenta"
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert result["banco"] == "Santander"

    def test_process_bank_statement_pdf_identifies_banorte(self):
        """Prueba que se identifique correctamente el banco Banorte"""
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = "Banorte Estado de Cuenta"
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert result["banco"] == "Banorte"

    def test_process_bank_statement_pdf_unknown_bank(self):
        """Prueba que se maneje correctamente un banco desconocido"""
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = "Banco Desconocido Estado de Cuenta"
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert result["banco"] == "Desconocido"

    def test_process_bank_statement_pdf_extracts_transactions(self):
        """Prueba que se extraigan transacciones del texto del PDF"""
        transaction_text = """
        04-Jun-2025  04-Jun-2025  SU PAGO GRACIAS SPEI A CTA CLABE XXXXXXXX1179  + $9,153.00
        05-Jun-2025  05-Jun-2025  COMPRA TARJETA OXXO MONTERREY  - $150.00
        06-Jun-2025  06-Jun-2025  RETIRO CAJERO AUTOMATICO  - $500.00
        """
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = transaction_text
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert len(result["transacciones"]) == 3
                assert result["transacciones"][0]["fecha_operacion"] == "04-Jun-2025"
                assert result["transacciones"][0]["descripcion"] == "SU PAGO GRACIAS SPEI A CTA CLABE XXXXXXXX1179"
                assert result["transacciones"][0]["monto"] == 9153.00
                assert result["transacciones"][0]["tipo"] == "abono"

    def test_process_bank_statement_pdf_handles_cargo_transactions(self):
        """Prueba que se manejen correctamente las transacciones de cargo"""
        transaction_text = "05-Jun-2025  05-Jun-2025  COMPRA TARJETA OXXO MONTERREY  - $150.00"
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = transaction_text
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert len(result["transacciones"]) == 1
                assert result["transacciones"][0]["monto"] == -150.00
                assert result["transacciones"][0]["tipo"] == "cargo"

    def test_process_bank_statement_pdf_handles_empty_pdf(self):
        """Prueba que se maneje correctamente un PDF vacío"""
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = ""
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
            
            assert result["banco"] == "Desconocido"
            assert len(result["transacciones"]) == 0

    def test_process_bank_statement_pdf_handles_none_text(self):
        """Prueba que se maneje correctamente cuando extract_text devuelve None"""
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = None
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
            
            assert result["banco"] == "Desconocido"
            assert len(result["transacciones"]) == 0


class TestOpenAICategorization:
    """Pruebas para la categorización con OpenAI"""

    @patch('openai.OpenAI')
    def test_categorize_transaction_openai_success(self, mock_openai_class):
        """Prueba la categorización exitosa con OpenAI"""
        # Configurar el mock del cliente OpenAI
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "supermercado"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        categoria = categorize_transaction_openai("COMPRA TARJETA OXXO MONTERREY", "fake_api_key")
        
        assert categoria == "supermercado"
        mock_client.chat.completions.create.assert_called_once()

    @patch('openai.OpenAI')
    def test_categorize_transaction_openai_handles_error(self, mock_openai_class):
        """Prueba que se maneje correctamente un error de OpenAI"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        # Ahora debería manejar el error y usar categorización básica
        categoria = categorize_transaction_openai("COMPRA TARJETA OXXO MONTERREY", "fake_api_key")
        
        # Debería devolver una categoría basada en palabras clave
        assert categoria == "conveniencia"

    def test_categorize_transaction_openai_fallback_categorization(self):
        """Prueba la categorización de respaldo basada en palabras clave"""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai_class.return_value = mock_client
            
            # Probar diferentes tipos de transacciones
            assert categorize_transaction_openai("COMPRA TARJETA OXXO", "fake_api_key") == "conveniencia"
            assert categorize_transaction_openai("RESTAURANTE PIZZA HUT", "fake_api_key") == "restaurante"
            assert categorize_transaction_openai("UBER TRIP", "fake_api_key") == "transporte"
            assert categorize_transaction_openai("SU PAGO SPEI", "fake_api_key") == "ingreso"
            assert categorize_transaction_openai("RETIRO CAJERO", "fake_api_key") == "retiro"
            assert categorize_transaction_openai("TRANSACCION DESCONOCIDA", "fake_api_key") == "otros"


class TestAITransactionExtraction:
    """Pruebas para la extracción de transacciones con AI"""

    @patch('openai.OpenAI')
    def test_extract_transactions_with_ai_success(self, mock_openai_client):
        """Prueba la extracción exitosa de transacciones con AI"""
        # Configurar el mock
        mock_client = Mock()
        mock_openai_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps([
            {
                "fecha_operacion": "04-Jun-2025",
                "fecha_cargo": "04-Jun-2025",
                "descripcion": "SU PAGO GRACIAS SPEI",
                "monto": 9153.00
            }
        ])
        mock_client.chat.completions.create.return_value = mock_response
        
        transactions = extract_transactions_with_ai("BBVA MEXICO ESTADO DE CUENTA...")
        
        assert len(transactions) == 1
        assert transactions[0]["fecha_operacion"] == "04-Jun-2025"
        assert transactions[0]["monto"] == 9153.00

    @patch('openai.OpenAI')
    def test_extract_transactions_with_ai_invalid_json(self, mock_openai_client):
        """Prueba que se maneje correctamente una respuesta JSON inválida de OpenAI"""
        mock_client = Mock()
        mock_openai_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "respuesta inválida no JSON"
        mock_client.chat.completions.create.return_value = mock_response
        
        transactions = extract_transactions_with_ai("BBVA MEXICO ESTADO DE CUENTA...")
        
        assert transactions == []

    @patch('openai.OpenAI')
    def test_extract_transactions_with_ai_api_error(self, mock_openai_client):
        """Prueba que se maneje correctamente un error de la API de OpenAI"""
        mock_client = Mock()
        mock_openai_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        transactions = extract_transactions_with_ai("BBVA MEXICO ESTADO DE CUENTA...")
        
        assert transactions == []


class TestOCRTextExtraction:
    """Pruebas para la extracción de texto con OCR"""

    @patch('app.routers.convert_from_bytes')
    @patch('app.routers.pytesseract.image_to_string')
    def test_extract_text_with_ocr_success(self, mock_tesseract, mock_convert):
        """Prueba la extracción exitosa de texto con OCR"""
        # Configurar mocks
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_tesseract.return_value = "Texto extraído con OCR"
        
        text = extract_text_with_ocr(b"fake_pdf_content")
        
        assert text == "Texto extraído con OCR\n"
        mock_convert.assert_called_once_with(b"fake_pdf_content")
        mock_tesseract.assert_called_once()

    @patch('app.routers.convert_from_bytes')
    def test_extract_text_with_ocr_conversion_error(self, mock_convert):
        """Prueba que se maneje correctamente un error en la conversión de PDF a imagen"""
        mock_convert.side_effect = Exception("Conversion error")
        
        text = extract_text_with_ocr(b"fake_pdf_content")
        
        assert text == ""

    @patch('app.routers.convert_from_bytes')
    @patch('app.routers.pytesseract.image_to_string')
    def test_extract_text_with_ocr_tesseract_error(self, mock_tesseract, mock_convert):
        """Prueba que se maneje correctamente un error de Tesseract"""
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_tesseract.side_effect = Exception("Tesseract error")
        
        text = extract_text_with_ocr(b"fake_pdf_content")
        
        assert text == ""


class TestPDFProcessingIntegration:
    """Pruebas de integración para el procesamiento de PDFs"""

    def test_full_pdf_processing_workflow(self):
        """Prueba el flujo completo de procesamiento de PDFs"""
        # Crear un archivo PDF temporal para pruebas
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(b"%PDF-1.4\n%Test PDF content")
            temp_pdf_path = temp_pdf.name
        
        try:
            with patch('pdfplumber.open') as mock_pdf:
                mock_pdf_instance = Mock()
                mock_pdf_instance.pages = [Mock()]
                mock_pdf_instance.pages[0].extract_text.return_value = """
                BBVA MEXICO
                ESTADO DE CUENTA
                04-Jun-2025  04-Jun-2025  SU PAGO GRACIAS SPEI  + $9,153.00
                05-Jun-2025  05-Jun-2025  COMPRA TARJETA OXXO  - $150.00
                """
                mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
                
                with patch('app.main.categorize_transaction_openai') as mock_categorize:
                    mock_categorize.return_value = "supermercado"
                    
                    result = process_bank_statement_pdf(temp_pdf_path, "fake_api_key")
                    
                    assert result["banco"] == "BBVA"
                    assert len(result["transacciones"]) == 2
                    assert result["transacciones"][0]["tipo"] == "abono"
                    assert result["transacciones"][1]["tipo"] == "cargo"
        
        finally:
            # Limpiar el archivo temporal
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 