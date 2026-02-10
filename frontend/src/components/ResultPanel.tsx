"use client";

interface ProcessResult {
  case_id: string;
  status: string;
  extracted_data: {
    beschikkingsnummer?: string;
    overtreding_datum?: string;
    feitcode?: string;
    omschrijving?: string;
    locatie?: string;
    bedrag?: number;
    instantie?: string;
  };
  legal_analysis: string;
  success_probability: number;
  bezwaarschrift_path?: string;
  message: string;
}

interface Props {
  result: ProcessResult;
  onReset: () => void;
}

export default function ResultPanel({ result, onReset }: Props) {
  const probabilityPercent = Math.round(result.success_probability * 100);
  const probabilityColor =
    probabilityPercent >= 60
      ? "text-green-600"
      : probabilityPercent >= 30
      ? "text-yellow-600"
      : "text-red-600";

  return (
    <div className="space-y-6">
      {/* Summary card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Analyse Resultaat</h2>

        <div className="flex items-center gap-4 mb-4">
          <div className="text-center">
            <div className={`text-3xl font-bold ${probabilityColor}`}>
              {probabilityPercent}%
            </div>
            <div className="text-xs text-gray-500">Geschatte slagingskans</div>
          </div>
          <div className="flex-1">
            <p className="text-sm text-gray-700">{result.message}</p>
            <p className="text-xs text-gray-400 mt-1">
              Zaak ID: {result.case_id}
            </p>
          </div>
        </div>

        {/* Extracted fine details */}
        <div className="bg-gray-50 rounded p-4 mb-4">
          <h3 className="font-medium text-sm mb-2">Boete-gegevens</h3>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <dt className="text-gray-500">Beschikkingsnummer:</dt>
            <dd>{result.extracted_data.beschikkingsnummer || "N/A"}</dd>

            <dt className="text-gray-500">Datum overtreding:</dt>
            <dd>{result.extracted_data.overtreding_datum || "N/A"}</dd>

            <dt className="text-gray-500">Feitcode:</dt>
            <dd>{result.extracted_data.feitcode || "N/A"}</dd>

            <dt className="text-gray-500">Omschrijving:</dt>
            <dd>{result.extracted_data.omschrijving || "N/A"}</dd>

            <dt className="text-gray-500">Locatie:</dt>
            <dd>{result.extracted_data.locatie || "N/A"}</dd>

            <dt className="text-gray-500">Bedrag:</dt>
            <dd>
              {result.extracted_data.bedrag
                ? `\u20AC ${result.extracted_data.bedrag.toFixed(2)}`
                : "N/A"}
            </dd>

            <dt className="text-gray-500">Instantie:</dt>
            <dd>{result.extracted_data.instantie || "N/A"}</dd>
          </dl>
        </div>
      </div>

      {/* Legal analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Juridische Analyse</h2>
        <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 rounded p-4 overflow-x-auto">
          {result.legal_analysis}
        </pre>
      </div>

      {/* Bezwaarschrift download */}
      {result.bezwaarschrift_path && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-medium text-green-800 mb-2">
            Bezwaarschrift gegenereerd
          </h3>
          <p className="text-sm text-green-700 mb-3">
            Uw bezwaarschrift is succesvol gegenereerd en kan worden gedownload.
          </p>
          <p className="text-xs text-green-600">
            Bestandslocatie: {result.bezwaarschrift_path}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={onReset}
          className="px-6 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
        >
          Nieuwe boete verwerken
        </button>
      </div>
    </div>
  );
}
