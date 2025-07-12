#!/usr/bin/env python3
"""
Script para limpiar todas las transacciones de la base de datos.
Útil para eliminar datos de prueba antes de nuevas validaciones.
"""

from app.database import SessionLocal
from app.models import Transaction, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def limpiar_base_datos():
    """Limpia todas las transacciones de la base de datos"""
    db = SessionLocal()
    try:
        # Contar transacciones antes de limpiar
        total_transacciones = db.query(Transaction).count()
        logger.info(f'📊 Total de transacciones antes de limpiar: {total_transacciones}')
        
        # Mostrar usuarios existentes
        usuarios = db.query(User).all()
        logger.info(f'👥 Usuarios en la base de datos: {len(usuarios)}')
        for usuario in usuarios:
            logger.info(f'  - {usuario.email} (ID: {usuario.id})')
        
        if total_transacciones > 0:
            # Eliminar todas las transacciones
            transacciones_eliminadas = db.query(Transaction).delete()
            db.commit()
            
            logger.info(f'🗑️ Transacciones eliminadas: {transacciones_eliminadas}')
            logger.info('✅ Base de datos limpiada exitosamente')
        else:
            logger.info('ℹ️ No hay transacciones para eliminar')
        
        # Verificar que se eliminaron todas
        total_despues = db.query(Transaction).count()
        logger.info(f'📊 Total de transacciones después de limpiar: {total_despues}')
        
    except Exception as e:
        logger.error(f'❌ Error limpiando base de datos: {e}')
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    logger.info('🧹 Iniciando limpieza de base de datos...')
    limpiar_base_datos()
    logger.info('🎉 Limpieza completada') 