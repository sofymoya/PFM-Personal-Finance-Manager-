import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# Importar solo las funciones que sabemos que funcionan
from app.main import process_bank_statement_pdf, categorize_transaction_openai


class TestPDFProcessing:
    """Pruebas unitarias para el procesamiento de PDFs"""

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

    def test_process_bank_statement_pdf_extracts_transactions_original_format(self):
        """Prueba que se extraigan transacciones del formato original"""
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

    def test_process_bank_statement_pdf_extracts_transactions_simplified_format(self):
        """Prueba que se extraigan transacciones del formato simplificado"""
        transaction_text = """
        04-Jun-2025  SU PAGO GRACIAS SPEI  + $9,153.00
        05-Jun-2025  COMPRA TARJETA OXXO  - $150.00
        """
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = transaction_text
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert len(result["transacciones"]) == 2
                assert result["transacciones"][0]["fecha_operacion"] == "04-Jun-2025"
                assert result["transacciones"][0]["descripcion"] == "SU PAGO GRACIAS SPEI"
                assert result["transacciones"][0]["monto"] == 9153.00

    def test_process_bank_statement_pdf_extracts_transactions_no_dollar_sign(self):
        """Prueba que se extraigan transacciones sin símbolo de peso"""
        transaction_text = """
        04-Jun-2025  SU PAGO GRACIAS SPEI  + 9,153.00
        05-Jun-2025  COMPRA TARJETA OXXO  - 150.00
        """
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = transaction_text
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                assert len(result["transacciones"]) == 2
                assert result["transacciones"][0]["monto"] == 9153.00
                assert result["transacciones"][1]["monto"] == -150.00

    def test_process_bank_statement_pdf_handles_cargo_transactions(self):
        """Prueba que se manejen correctamente las transacciones de cargo"""
        transaction_text = "05-Jun-2025  COMPRA TARJETA OXXO MONTERREY  - $150.00"
        
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

    def test_process_bank_statement_pdf_handles_invalid_lines(self):
        """Prueba que se manejen correctamente líneas inválidas"""
        transaction_text = """
        Línea inválida sin formato
        04-Jun-2025  SU PAGO GRACIAS SPEI  + $9,153.00
        Otra línea inválida
        """
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf_instance = Mock()
            mock_pdf_instance.pages = [Mock()]
            mock_pdf_instance.pages[0].extract_text.return_value = transaction_text
            mock_pdf.return_value.__enter__.return_value = mock_pdf_instance
            
            with patch('app.main.categorize_transaction_openai') as mock_categorize:
                mock_categorize.return_value = "supermercado"
                
                result = process_bank_statement_pdf("fake_path.pdf", "fake_api_key")
                
                # Debería extraer solo la línea válida
                assert len(result["transacciones"]) == 1
                assert result["transacciones"][0]["fecha_operacion"] == "04-Jun-2025"


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 