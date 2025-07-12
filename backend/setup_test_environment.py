#!/usr/bin/env python3
"""
Script para configurar el entorno de pruebas completo:
1. Limpiar base de datos
2. Crear usuarios de prueba
3. Verificar que el backend esté corriendo
4. Ejecutar pruebas
"""

import subprocess
import time
import requests
import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEnvironmentSetup:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.backend_process = None
        
    def check_backend_running(self) -> bool:
        """Verifica si el backend está corriendo"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_backend(self):
        """Inicia el backend si no está corriendo"""
        if self.check_backend_running():
            logger.info("✅ Backend ya está corriendo")
            return True
        
        logger.info("🚀 Iniciando backend...")
        try:
            # Activar entorno virtual y ejecutar uvicorn
            cmd = [
                "source", "venv/bin/activate", "&&",
                "python", "-m", "uvicorn", "app.main:app", 
                "--reload", "--host", "0.0.0.0", "--port", "8000"
            ]
            
            # Ejecutar en background
            self.backend_process = subprocess.Popen(
                " ".join(cmd),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar a que inicie
            for i in range(30):  # 30 segundos máximo
                time.sleep(1)
                if self.check_backend_running():
                    logger.info("✅ Backend iniciado exitosamente")
                    return True
                logger.info(f"⏳ Esperando backend... ({i+1}/30)")
            
            logger.error("❌ Backend no inició en 30 segundos")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error iniciando backend: {e}")
            return False
    
    def stop_backend(self):
        """Detiene el backend"""
        if self.backend_process:
            logger.info("🛑 Deteniendo backend...")
            self.backend_process.terminate()
            self.backend_process.wait()
            logger.info("✅ Backend detenido")
    
    def clean_database(self):
        """Limpia la base de datos"""
        logger.info("🧹 Limpiando base de datos...")
        try:
            result = subprocess.run([
                "source", "venv/bin/activate", "&&", "python", "limpiar_db.py"
            ], shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Base de datos limpiada")
            else:
                logger.error(f"❌ Error limpiando base de datos: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando limpieza: {e}")
    
    def create_test_users(self):
        """Crea usuarios de prueba"""
        logger.info("👥 Creando usuarios de prueba...")
        try:
            result = subprocess.run([
                "source", "venv/bin/activate", "&&", "python", "create_user.py"
            ], shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Usuarios de prueba creados")
            else:
                logger.info("ℹ️ Usuarios ya existen o error (puede ser normal)")
                
        except Exception as e:
            logger.error(f"❌ Error creando usuarios: {e}")
    
    def run_tests(self):
        """Ejecuta las pruebas"""
        logger.info("🧪 Ejecutando pruebas...")
        try:
            result = subprocess.run([
                "source", "venv/bin/activate", "&&", "python", "test_multi_bank.py"
            ], shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Pruebas completadas exitosamente")
                logger.info("📄 Salida de las pruebas:")
                print(result.stdout)
            else:
                logger.error(f"❌ Error en las pruebas: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando pruebas: {e}")
    
    def setup_and_run(self):
        """Configura el entorno y ejecuta las pruebas"""
        logger.info("🔧 Configurando entorno de pruebas...")
        
        try:
            # 1. Limpiar base de datos
            self.clean_database()
            
            # 2. Crear usuarios de prueba
            self.create_test_users()
            
            # 3. Verificar/iniciar backend
            if not self.start_backend():
                logger.error("❌ No se pudo iniciar el backend")
                return False
            
            # 4. Ejecutar pruebas
            self.run_tests()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("⏹️ Interrumpido por el usuario")
            return False
        except Exception as e:
            logger.error(f"❌ Error en configuración: {e}")
            return False
        finally:
            # Limpiar al final
            self.stop_backend()

def main():
    """Función principal"""
    setup = TestEnvironmentSetup()
    
    try:
        success = setup.setup_and_run()
        if success:
            logger.info("🎉 Configuración y pruebas completadas exitosamente")
        else:
            logger.error("💥 Error en la configuración o pruebas")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️ Interrumpido por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main() 