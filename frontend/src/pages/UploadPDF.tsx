import React, { useState } from 'react';
import axios from 'axios';

const UploadPDF: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Obtener el token del usuario autenticado (ajusta según tu auth)
  const token = localStorage.getItem('token');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (!file) {
      setError('Selecciona un archivo PDF.');
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post(
        'http://localhost:8000/upload_pdf',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al subir el PDF.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Subir estado de cuenta bancario (PDF)</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-700 border border-gray-300 rounded cursor-pointer focus:outline-none"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Subiendo...' : 'Subir PDF'}
        </button>
      </form>
      {error && <div className="mt-4 text-red-600">{error}</div>}
      {result && (
        <div className="mt-6 p-4 bg-green-100 rounded">
          <div className="font-semibold">Archivo: {result.filename}</div>
          <div>Banco detectado: <span className="font-semibold">{result.banco}</span></div>
          <div>Transacciones guardadas: <span className="font-semibold">{result.transacciones_guardadas?.length || 0}</span></div>
          <ul className="mt-2 list-disc list-inside text-sm">
            {result.transacciones_guardadas?.slice(0, 5).map((t: any) => (
              <li key={t.id}>{t.date} - {t.description} (${t.amount}) [{t.category}]</li>
            ))}
            {result.transacciones_guardadas?.length > 5 && <li>...y más</li>}
          </ul>
        </div>
      )}
    </div>
  );
};

export default UploadPDF; 