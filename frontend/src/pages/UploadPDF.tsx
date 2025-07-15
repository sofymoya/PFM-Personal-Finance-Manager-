import React, { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import image from "../assets/image.svg";
import vector0 from "../assets/vector-0.svg";
import { formatPesos } from '../utils/formatters';

interface Transaction {
  fecha_operacion: string;
  descripcion: string;
  monto: number;
  tipo: string;
  categoria: string;
  banco: string;
}

export const UploadBank = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [uploadResult, setUploadResult] = useState<{
    success: boolean;
    message: string;
    transactionsCount?: number;
  } | null>(null);
  const [fileError, setFileError] = useState<string | null>(null); // <-- NUEVO
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

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
      setFileError(null);
    } else {
      setFile(null);
      setFileError('Solo se permiten archivos PDF.');
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setFileError(null);
    } else if (selectedFile) {
      setFile(null);
      setFileError('Solo se permiten archivos PDF.');
    }
  };

  const handleSelectFileClick = () => {
    fileInputRef.current?.click();
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
        // Mapeo defensivo para manejar diferentes nombres de campos del backend
        // El backend devuelve las transacciones en 'transacciones_guardadas'
        const backendTransactions = result.transacciones_guardadas || result.transactions || [];
        
        const txs = backendTransactions.map((t: any) => ({
          fecha_operacion: t.fecha_operacion || t.fecha || t.date || t.fecha_transaccion || '',
          descripcion: t.descripcion || t.description || t.desc || t.concepto || '',
          monto: t.monto ?? t.amount ?? t.importe ?? t.valor ?? 0,
          tipo: t.tipo || t.type || t.nature || '',
          categoria: t.categoria || t.category || t.cat || '',
          banco: t.banco || t.bank || t.entidad || '',
        }));
        
        if (txs.length === 0) {
          setUploadResult({
            success: false,
            message: 'No se encontraron transacciones en tu PDF. Intenta con otro archivo o revisa el estado de cuenta.'
          });
        } else {
          setUploadResult({
            success: true,
            message: `PDF procesado exitosamente. Se encontraron ${txs.length} transacciones.`,
            transactionsCount: txs.length
          });
        }
        setTransactions(txs);
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

  return (
    <div className="flex flex-col items-start relative bg-white">
      <div className="flex flex-col min-h-[800px] items-start relative self-stretch w-full flex-[0_0_auto] bg-white">
        <div className="flex flex-col items-start relative self-stretch w-full flex-[0_0_auto]">
          {/* Header with Navigation */}
          <div className="w-full border-b border-[#e5e8ea] px-10 py-3 flex items-center justify-between">
            <span className="font-bold text-lg text-[#111416]">FinTrack</span>
            
            {/* Navigation Buttons */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                🏠 Dashboard
              </button>
              <button
                onClick={() => navigate('/transactions')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                📊 Transactions
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                🚪 Logout
              </button>
            </div>
          </div>

          <div className="items-start justify-center px-40 py-5 flex-1 grow flex relative self-stretch w-full">
            <div className="flex flex-col max-w-[960px] w-[960px] items-start px-0 py-5 relative">
              <div className="flex flex-wrap items-start justify-around gap-[12px_12px] p-4 relative self-stretch w-full flex-[0_0_auto]">
                <div className="inline-flex min-w-72 items-start flex-[0_0_auto] flex-col relative">
                  <div className="relative self-stretch mt-[-1.00px] font-bold text-[#111416] text-[32px] tracking-[0] leading-10 whitespace-nowrap">
                    Upload Bank Statement
                  </div>
                </div>
              </div>

              <div className="flex flex-col items-start p-4 relative self-stretch w-full flex-[0_0_auto]">
                <div 
                  className={`flex items-center gap-6 px-6 py-14 self-stretch w-full flex-[0_0_auto] rounded-xl border-2 border-dashed flex-col relative transition-colors ${
                    isDragOver 
                      ? 'border-blue-400 bg-blue-50' 
                      : file 
                        ? 'border-green-400 bg-green-50'
                        : 'border-[#dbe0e5] hover:border-gray-400'
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  {file ? (
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                        <span className="text-2xl">✅</span>
                      </div>
                      <div className="text-center">
                        <p className="font-bold text-[#111416] text-lg">
                          {file.name}
                        </p>
                        <p className="text-[#637787] text-sm">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <button
                        onClick={() => setFile(null)}
                        className="min-w-[84px] h-10 items-center justify-center px-4 py-0 relative bg-[#eff2f4] rounded-[20px] overflow-hidden font-bold text-[#111416] text-sm"
                      >
                        Change File
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
                        <span className="text-2xl">📄</span>
                      </div>
                      <div className="text-center">
                        <p className="font-bold text-[#111416] text-lg">
                          Drag and drop your PDF here
                        </p>
                        <p className="text-[#111416] text-sm">
                          Or click to browse
                        </p>
                      </div>
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileSelect}
                        className="hidden"
                        id="file-input"
                        ref={fileInputRef}
                      />
                      <button
                        type="button"
                        onClick={handleSelectFileClick}
                        className="min-w-[84px] h-10 items-center justify-center px-4 py-0 relative bg-[#eff2f4] rounded-[20px] overflow-hidden font-bold text-[#111416] text-sm cursor-pointer"
                      >
                        Select File
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {file && (
                <div className="flex flex-col items-center pt-1 pb-3 px-4 relative self-stretch w-full flex-[0_0_auto]">
                  <button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="min-w-[120px] h-10 items-center justify-center px-4 py-0 relative bg-blue-600 text-white rounded-[20px] overflow-hidden font-bold text-sm hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {uploading ? 'Processing...' : 'Process PDF'}
                  </button>
                </div>
              )}

              <div className="flex flex-col items-center pt-1 pb-3 px-4 relative self-stretch w-full flex-[0_0_auto]">
                <p className="relative self-stretch mt-[-1.00px] font-normal text-[#637787] text-sm text-center tracking-[0] leading-[21px]">
                  We support PDF format only
                </p>
              </div>

              {/* Feedback de error de archivo */}
              {fileError && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2">
                  <span className="text-xl">❌</span>
                  <span className="text-red-800 font-medium">{fileError}</span>
                </div>
              )}

              {/* Upload Result */}
              {uploadResult && (
                <div className="flex flex-col items-start p-4 relative self-stretch w-full flex-[0_0_auto]">
                  <div className={`p-4 rounded-lg w-full ${
                    uploadResult.success 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        uploadResult.success ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        <span className="text-lg">
                          {uploadResult.success ? '✅' : '❌'}
                        </span>
                      </div>
                      <div>
                        <p className={`font-medium ${
                          uploadResult.success ? 'text-green-800' : 'text-red-800'
                        }`}>
                          {uploadResult.message}
                        </p>
                        {uploadResult.success && uploadResult.transactionsCount !== undefined && (
                          <p className="text-sm text-green-600">
                            {uploadResult.transactionsCount} transacciones extraídas
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Transactions Table */}
              {transactions.length > 0 && (
                <div className="flex flex-col items-start p-4 relative self-stretch w-full flex-[0_0_auto]">
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border border-gray-200 rounded-lg">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Fecha
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Descripción
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Monto
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Categoría
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {transactions.map((transaction, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {transaction.fecha_operacion}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {transaction.descripcion}
                            </td>
                            <td className={`px-4 py-3 text-sm font-medium ${
                              transaction.monto < 0 ? 'text-red-600' : 'text-green-600'
                            }`}>
                              {formatPesos(transaction.monto)}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {transaction.categoria}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadBank; 