"use client";

import { useCallback, useState } from "react";

interface Props {
  userId: string;
  onUploaded: (fineId: string) => void;
  demoMode?: boolean;
}

export default function FileUpload({ userId, onUploaded, demoMode }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [extractedData, setExtractedData] = useState<Record<
    string,
    string | number | boolean
  > | null>(null);

  const uploadFile = async (file: File) => {
    setUploading(true);
    setError(null);
    setFileName(file.name);

    if (demoMode) {
      await new Promise((r) => setTimeout(r, 1500));
      const demoData = {
        id: "demo-fine-" + Math.random().toString(36).slice(2, 10),
        beschikkingsnummer: "9876543210",
        feitcode: "VA020",
        bedrag: 95.0,
        locatie: "A2 hectometerpaal 43.2, gemeente Utrecht",
        instantie: "Politie Eenheid Midden-Nederland",
      };
      setExtractedData(demoData);
      onUploaded(demoData.id);
      setUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`/api/upload-fine?user_id=${userId}`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload mislukt.");
      }

      const data = await res.json();
      setExtractedData(data);
      onUploaded(data.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload mislukt.");
      setFileName(null);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files[0];
      if (file) uploadFile(file);
    },
    [userId, demoMode]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Upload Verkeersboete</h2>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
          dragActive
            ? "border-brand-500 bg-brand-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        {uploading ? (
          <div className="text-gray-500">
            <div className="animate-pulse">
              Bezig met uploaden en OCR-verwerking...
            </div>
          </div>
        ) : fileName ? (
          <div className="text-green-600">
            Bestand ge&uuml;pload: <strong>{fileName}</strong>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-600">
              Sleep uw CJIB-boete hierheen of klik om te selecteren
            </p>
            <p className="text-xs text-gray-400">
              Ondersteunde formaten: JPEG, PNG, TIFF, PDF
            </p>
            <label className="inline-block px-4 py-2 bg-brand-600 text-white rounded cursor-pointer hover:bg-brand-700 text-sm">
              Bestand kiezen
              <input
                type="file"
                accept="image/jpeg,image/png,image/tiff,application/pdf"
                onChange={handleChange}
                className="hidden"
              />
            </label>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
          {error}
        </div>
      )}

      {extractedData && (
        <div className="mt-4 bg-gray-50 rounded p-4">
          <h3 className="font-medium text-sm mb-2">
            Ge&euml;xtraheerde gegevens:
          </h3>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            {extractedData.beschikkingsnummer && (
              <>
                <dt className="text-gray-500">Beschikkingsnummer:</dt>
                <dd>{String(extractedData.beschikkingsnummer)}</dd>
              </>
            )}
            {extractedData.feitcode && (
              <>
                <dt className="text-gray-500">Feitcode:</dt>
                <dd>{String(extractedData.feitcode)}</dd>
              </>
            )}
            {extractedData.bedrag && (
              <>
                <dt className="text-gray-500">Bedrag:</dt>
                <dd>&euro; {String(extractedData.bedrag)}</dd>
              </>
            )}
            {extractedData.locatie && (
              <>
                <dt className="text-gray-500">Locatie:</dt>
                <dd>{String(extractedData.locatie)}</dd>
              </>
            )}
            {extractedData.instantie && (
              <>
                <dt className="text-gray-500">Instantie:</dt>
                <dd>{String(extractedData.instantie)}</dd>
              </>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}
