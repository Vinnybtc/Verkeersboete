"use client";

import { useState } from "react";

interface UserData {
  id: string;
  name: string;
  email: string;
  address?: string;
  postal_code?: string;
  city?: string;
  phone?: string;
}

interface Props {
  onRegistered: (user: UserData) => void;
}

export default function UserForm({ onRegistered }: Props) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    address: "",
    postal_code: "",
    city: "",
    phone: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authChecked) {
      setError("U moet de machtiging accepteren om door te gaan.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create user
      const res = await fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Registratie mislukt.");
      }

      const user: UserData = await res.json();

      // Sign authorization
      await fetch("/api/users/authorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, signed: true }),
      });

      onRegistered(user);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Er is een fout opgetreden.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Registratie</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Naam *
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              E-mail *
            </label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Adres
            </label>
            <input
              type="text"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Postcode
            </label>
            <input
              type="text"
              value={form.postal_code}
              onChange={(e) =>
                setForm({ ...form, postal_code: e.target.value })
              }
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              placeholder="1234 AB"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Plaats
            </label>
            <input
              type="text"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telefoon
            </label>
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="border-t pt-4 mt-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={authChecked}
              onChange={(e) => setAuthChecked(e.target.checked)}
              className="mt-1"
            />
            <span className="text-sm text-gray-600">
              Ik machtig de Verkeersboete AI Agent om namens mij bezwaar te maken
              tegen de door mij geüploade verkeersboete(s). Ik begrijp dat dit een
              geautomatiseerde dienst is en geen vervanging voor persoonlijk
              juridisch advies. Mijn gegevens worden verwerkt conform de AVG.
            </span>
          </label>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Bezig..." : "Registreren & Machtiging Ondertekenen"}
        </button>
      </form>
    </div>
  );
}
