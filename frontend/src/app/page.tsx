"use client";

import { useState } from "react";
import FileUpload from "@/components/FileUpload";
import UserForm from "@/components/UserForm";
import ResultPanel from "@/components/ResultPanel";

type Step = "register" | "upload" | "result";

interface UserData {
  id: string;
  name: string;
  email: string;
  address?: string;
  postal_code?: string;
  city?: string;
  phone?: string;
}

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

export default function Home() {
  const [step, setStep] = useState<Step>("register");
  const [user, setUser] = useState<UserData | null>(null);
  const [fineId, setFineId] = useState<string | null>(null);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUserRegistered = (userData: UserData) => {
    setUser(userData);
    setStep("upload");
    setError(null);
  };

  const handleFileUploaded = (uploadedFineId: string) => {
    setFineId(uploadedFineId);
    setError(null);
  };

  const handleProcess = async () => {
    if (!user || !fineId) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/process-fine?fine_id=${fineId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Verwerking mislukt.");
      }

      const data: ProcessResult = await res.json();
      setResult(data);
      setStep("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Er is een fout opgetreden.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep("register");
    setUser(null);
    setFineId(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-8">
      {/* Progress indicator */}
      <div className="flex items-center gap-2 text-sm">
        <span
          className={`px-3 py-1 rounded-full ${
            step === "register"
              ? "bg-brand-600 text-white"
              : "bg-gray-200 text-gray-600"
          }`}
        >
          1. Registratie
        </span>
        <span className="text-gray-300">&rarr;</span>
        <span
          className={`px-3 py-1 rounded-full ${
            step === "upload"
              ? "bg-brand-600 text-white"
              : "bg-gray-200 text-gray-600"
          }`}
        >
          2. Upload boete
        </span>
        <span className="text-gray-300">&rarr;</span>
        <span
          className={`px-3 py-1 rounded-full ${
            step === "result"
              ? "bg-brand-600 text-white"
              : "bg-gray-200 text-gray-600"
          }`}
        >
          3. Resultaat
        </span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Step 1: Registration */}
      {step === "register" && (
        <UserForm onRegistered={handleUserRegistered} />
      )}

      {/* Step 2: Upload */}
      {step === "upload" && user && (
        <div className="space-y-6">
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            Welkom, {user.name}. Upload nu uw boete-document.
          </div>

          <FileUpload userId={user.id} onUploaded={handleFileUploaded} />

          {fineId && (
            <div className="flex gap-4">
              <button
                onClick={handleProcess}
                disabled={loading}
                className="px-6 py-2 bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50"
              >
                {loading ? "Bezig met analyseren..." : "Analyseer & Genereer Bezwaarschrift"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 3: Result */}
      {step === "result" && result && (
        <ResultPanel result={result} onReset={handleReset} />
      )}
    </div>
  );
}
