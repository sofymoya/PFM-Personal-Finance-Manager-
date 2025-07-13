import React, { useState, useCallback } from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

interface Transaction {
  fecha_operacion: string;
  descripcion: string;
  monto: number;
  tipo: string;
  categoria: string;
  banco: string;
}

const UploadPDF: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [uploadResult, setUploadResult] = useState<{
    success: boolean;
    message: string;
    transactionsCount?: number;
  } | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    const pdfFile = droppedFiles.find(f => f.type === 'application/pdf');
    
    if (pdfFile) {
      setFile(pdfFile);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setUploadResult(null);
    setTransactions([]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/upload_pdf', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadResult({
          success: true,
          message: `PDF procesado exitosamente. Se encontraron ${result.transactions?.length || 0} transacciones.`,
          transactionsCount: result.transactions?.length || 0
        });
        setTransactions(result.transactions || []);
      } else {
        setUploadResult({
          success: false,
          message: result.detail || 'Error al procesar el PDF'
        });
      }
    } catch (error) {
      setUploadResult({
        success: false,
        message: 'Error de conexión. Verifica que el servidor esté funcionando.'
      });
    } finally {
      setUploading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-MX');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Cargar PDF</h1>
          <p className="text-neutral-600">Sube tu estado de cuenta bancario para extraer transacciones</p>
        </div>
      </div>

      {/* Upload Area */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-neutral-900">Seleccionar Archivo</h2>
        </CardHeader>
        <CardBody>
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${isDragOver 
                ? 'border-primary-400 bg-primary-50' 
                : 'border-neutral-300 hover:border-neutral-400'
              }
              ${file ? 'border-success-400 bg-success-50' : ''}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {file ? (
              <div className="space-y-4">
                <div className="w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mx-auto">
                  <svg className="w-8 h-8 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg font-medium text-neutral-900">{file.name}</p>
                  <p className="text-sm text-neutral-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFile(null)}
                >
                  Cambiar archivo
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mx-auto">
                  <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg font-medium text-neutral-900">
                    Arrastra tu PDF aquí o haz clic para seleccionar
                  </p>
                  <p className="text-sm text-neutral-500">
                    Solo archivos PDF de estados de cuenta bancarios
                  </p>
                </div>
                                 <input
                   type="file"
                   accept=".pdf"
                   onChange={handleFileSelect}
                   className="hidden"
                   id="file-input"
                 />
                 <label htmlFor="file-input">
                   <Button variant="outline">
                     Seleccionar archivo
                   </Button>
                 </label>
              </div>
            )}
          </div>

          {file && (
            <div className="mt-6">
              <Button
                onClick={handleUpload}
                loading={uploading}
                disabled={!file || uploading}
                className="w-full"
                size="lg"
                icon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                }
              >
                {uploading ? 'Procesando...' : 'Procesar PDF'}
              </Button>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Upload Result */}
      {uploadResult && (
        <Card>
          <CardBody>
            <div className={`p-4 rounded-lg ${
              uploadResult.success 
                ? 'bg-success-50 border border-success-200' 
                : 'bg-error-50 border border-error-200'
            }`}>
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  uploadResult.success ? 'bg-success-100' : 'bg-error-100'
                }`}>
                  <svg className={`w-5 h-5 ${
                    uploadResult.success ? 'text-success-600' : 'text-error-600'
                  }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className={`font-medium ${
                    uploadResult.success ? 'text-success-800' : 'text-error-800'
                  }`}>
                    {uploadResult.message}
                  </p>
                  {uploadResult.success && uploadResult.transactionsCount !== undefined && (
                    <p className="text-sm text-success-600">
                      {uploadResult.transactionsCount} transacciones extraídas
                    </p>
                  )}
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Transactions Table */}
      {transactions.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-neutral-900">
              Transacciones Extraídas ({transactions.length})
            </h2>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-200">
                    <th className="text-left py-3 px-4 font-medium text-neutral-700">Fecha</th>
                    <th className="text-left py-3 px-4 font-medium text-neutral-700">Descripción</th>
                    <th className="text-left py-3 px-4 font-medium text-neutral-700">Categoría</th>
                    <th className="text-left py-3 px-4 font-medium text-neutral-700">Banco</th>
                    <th className="text-right py-3 px-4 font-medium text-neutral-700">Monto</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((transaction, index) => (
                    <tr key={index} className="border-b border-neutral-100 hover:bg-neutral-50">
                      <td className="py-3 px-4 text-sm text-neutral-600">
                        {formatDate(transaction.fecha_operacion)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm font-medium text-neutral-900">
                          {transaction.descripcion}
                        </div>
                        <div className="text-xs text-neutral-500">
                          {transaction.tipo}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700">
                          {transaction.categoria}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-neutral-600">
                        {transaction.banco}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`text-sm font-medium ${
                          transaction.monto < 0 ? 'text-error-600' : 'text-success-600'
                        }`}>
                          {formatCurrency(Math.abs(transaction.monto))}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Instructions */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-neutral-900">Instrucciones</h2>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-primary-600 text-sm font-medium">1</span>
              </div>
              <div>
                <p className="font-medium text-neutral-900">Descarga tu estado de cuenta</p>
                <p className="text-sm text-neutral-600">
                  Accede a tu banca en línea y descarga el estado de cuenta en formato PDF
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-primary-600 text-sm font-medium">2</span>
              </div>
              <div>
                <p className="font-medium text-neutral-900">Sube el archivo</p>
                <p className="text-sm text-neutral-600">
                  Arrastra el PDF aquí o haz clic para seleccionarlo desde tu computadora
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-primary-600 text-sm font-medium">3</span>
              </div>
              <div>
                <p className="font-medium text-neutral-900">Procesa y revisa</p>
                <p className="text-sm text-neutral-600">
                  Nuestro sistema extraerá automáticamente las transacciones y las categorizará
                </p>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default UploadPDF; 