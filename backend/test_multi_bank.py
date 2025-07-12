#!/usr/bin/env python3
"""
Script de prueba mejorado para validar extracción y guardado de transacciones
de múltiples bancos (Santander, HSBC, BBVA, etc.)
"""

import requests
import json
import os
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMultiBank:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        
    def test_login(self, email: str, password: str) -> bool:
        """Prueba el login para obtener un token"""
        login_data = {
            "username": email,
            "password": password
        }
        
        try:
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data["access_token"]
                logger.info(f"✅ Login exitoso para {email}")
                return True
            else:
                logger.error(f"❌ Error en login para {email}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error de conexión en login: {e}")
            return False
    
    def test_upload_pdf(self, pdf_path: str, expected_bank: Optional[str] = None) -> Dict:
        """Prueba subir un PDF y extraer transacciones"""
        if not self.token:
            logger.error("❌ No hay token de autenticación")
            return {"success": False, "error": "No token"}
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ Archivo no encontrado: {pdf_path}")
            return {"success": False, "error": "File not found"}
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
                response = self.session.post(f"{self.base_url}/upload_pdf", headers=headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ PDF subido exitosamente: {pdf_path}")
                logger.info(f"🏦 Banco detectado: {result.get('banco_detectado', 'Desconocido')}")
                logger.info(f"📊 Transacciones guardadas: {result.get('transacciones_guardadas', 0)}")
                
                # Validar banco esperado
                if expected_bank and result.get('banco_detectado') != expected_bank:
                    logger.warning(f"⚠️ Banco detectado ({result.get('banco_detectado')}) no coincide con esperado ({expected_bank})")
                
                return {
                    "success": True,
                    "banco_detectado": result.get('banco_detectado'),
                    "transacciones_guardadas": result.get('transacciones_guardadas', 0),
                    "total_transacciones": result.get('total_transacciones', 0)
                }
            else:
                logger.error(f"❌ Error subiendo PDF: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Error de conexión subiendo PDF: {e}")
            return {"success": False, "error": str(e)}
    
    def test_get_transactions(self) -> Dict:
        """Prueba obtener las transacciones del usuario"""
        if not self.token:
            logger.error("❌ No hay token de autenticación")
            return {"success": False, "error": "No token"}
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = self.session.get(f"{self.base_url}/transactions", headers=headers)
            
            if response.status_code == 200:
                transactions = response.json()
                logger.info(f"✅ Transacciones obtenidas: {len(transactions)}")
                return {"success": True, "transactions": transactions, "count": len(transactions)}
            else:
                logger.error(f"❌ Error obteniendo transacciones: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"❌ Error de conexión obteniendo transacciones: {e}")
            return {"success": False, "error": str(e)}
    
    def run_test_suite(self, test_cases: List[Dict]) -> Dict:
        """Ejecuta una suite completa de pruebas"""
        logger.info("🚀 Iniciando suite de pruebas multi-banco...")
        
        results = {
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "results": []
        }
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n📋 Prueba {i}/{len(test_cases)}: {test_case['name']}")
            
            # Login
            if not self.test_login(test_case['email'], test_case['password']):
                results["failed"] += 1
                results["results"].append({
                    "test": test_case['name'],
                    "status": "FAILED",
                    "error": "Login failed"
                })
                continue
            
            # Upload PDF
            upload_result = self.test_upload_pdf(
                test_case['pdf_path'], 
                test_case.get('expected_bank', None)
            )
            
            if upload_result["success"]:
                # Get transactions to verify
                trans_result = self.test_get_transactions()
                
                if trans_result["success"]:
                    results["passed"] += 1
                    results["results"].append({
                        "test": test_case['name'],
                        "status": "PASSED",
                        "banco_detectado": upload_result["banco_detectado"],
                        "transacciones_guardadas": upload_result["transacciones_guardadas"],
                        "total_transacciones": trans_result["count"]
                    })
                else:
                    results["failed"] += 1
                    results["results"].append({
                        "test": test_case['name'],
                        "status": "FAILED",
                        "error": "Failed to get transactions"
                    })
            else:
                results["failed"] += 1
                results["results"].append({
                    "test": test_case['name'],
                    "status": "FAILED",
                    "error": upload_result.get("error", "Upload failed")
                })
        
        # Resumen final
        logger.info(f"\n📊 RESUMEN DE PRUEBAS:")
        logger.info(f"✅ Exitosas: {results['passed']}")
        logger.info(f"❌ Fallidas: {results['failed']}")
        logger.info(f"📈 Tasa de éxito: {(results['passed']/results['total_tests']*100):.1f}%")
        
        return results

def main():
    """Función principal con casos de prueba predefinidos"""
    
    # Configurar casos de prueba
    test_cases = [
        {
            "name": "Santander - Estado de cuenta abril 2025-2.pdf",
            "email": "prueba_front@correo.com",
            "password": "claveFront123",
            "pdf_path": "uploaded_pdfs/Estado de cuenta abril 2025-2.pdf",
            "expected_bank": "Santander"
        }
        # Puedes agregar más casos aquí:
        # {
        #     "name": "HSBC - Estado de cuenta",
        #     "email": "prueba_front@correo.com", 
        #     "password": "claveFront123",
        #     "pdf_path": "uploaded_pdfs/hsbc_estado_cuenta.pdf",
        #     "expected_bank": "HSBC"
        # },
        # {
        #     "name": "BBVA - Estado de cuenta",
        #     "email": "prueba_front@correo.com",
        #     "password": "claveFront123", 
        #     "pdf_path": "uploaded_pdfs/bbva_estado_cuenta.pdf",
        #     "expected_bank": "BBVA"
        # }
    ]
    
    # Ejecutar pruebas
    tester = TestMultiBank()
    results = tester.run_test_suite(test_cases)
    
    # Guardar resultados en archivo
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Resultados guardados en test_results.json")

if __name__ == "__main__":
    main() 