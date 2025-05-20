import React, { useState } from 'react';
import { ViolationForm } from './components/ViolationForm';
export function App() {
  return <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">
          Violation Report
        </h1>
        <ViolationForm />
      </div>
    </div>;
}