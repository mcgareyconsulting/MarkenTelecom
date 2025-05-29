import React, { useState } from 'react';
import { PlusCircleIcon } from 'lucide-react';
import { ViolationItem } from './ViolationItem';

type Violation = {
  id: number;
  type: string;
  image: File | null;
  notes: string;
};

type AddressData = {
  line1: string;
  line2: string;
  city: string;
  state: string;
  zip: string;
  district: string;
};

export function ViolationForm() {
  const [address, setAddress] = useState<AddressData>({
    line1: '',
    line2: '',
    city: '',
    state: '',
    zip: '',
    district: '',
  });

  const [violations, setViolations] = useState<Violation[]>([{
    id: 1,
    type: '',
    image: null,
    notes: ''
  }]);

  // Add loading and error states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const districts = [
    {
      value: '',
      label: 'Select Metro District',
    },
    {
      value: 'waters_edge',
      label: 'Waters Edge Metro District',
    },
    {
      value: 'highlands_mead',
      label: 'Highlands Mead Metro District',
    },
  ];

  const handleAddressChange = (field: keyof AddressData) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setAddress((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));
  };

  const handleAddViolation = () => {
    const newId = violations.length > 0 ? Math.max(...violations.map(v => v.id)) + 1 : 1;
    setViolations([...violations, {
      id: newId,
      type: '',
      image: null,
      notes: ''
    }]);
  };

  const updateViolation = (id: number, updates: Partial<Violation>) => {
    setViolations(violations.map(violation => violation.id === id ? {
      ...violation,
      ...updates
    } : violation));
  };

  const removeViolation = (id: number) => {
    if (violations.length > 1) {
      setViolations(violations.filter(violation => violation.id !== id));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Reset states
    setError(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      // Validate form data
      if (!address.line1 || !address.city || !address.state || !address.zip || !address.district) {
        throw new Error('Please fill in all required address fields');
      }

      if (violations.length === 0) {
        throw new Error('At least one violation is required');
      }

      if (violations.some(v => !v.type)) {
        throw new Error('All violations must have a type selected');
      }

      // Create FormData object
      const formData = new FormData();

      // Add JSON data
      const jsonData = {
        address: {
          line1: address.line1,
          line2: address.line2,
          city: address.city,
          state: address.state,
          zip: address.zip,
          district: address.district
        },
        violations: violations.map(({ id, type, notes }) => ({
          id,
          type,
          notes
        }))
      };

      formData.append('data', JSON.stringify(jsonData));

      // Add image files with the correct keys
      violations.forEach((violation, index) => {
        if (violation.image) {
          formData.append(`violation_${index}_image`, violation.image);
        }
      });

      console.log('Submitting report with data:', formData);

      // Send the request to the backend
      const response = await fetch('/api/violations', {
        method: 'POST',
        body: formData,
      });

      let result: any = null;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        result = await response.json();
      }

      if (!response.ok) {
        throw new Error(result?.error || 'Failed to submit report');
      }

      console.log('Report submitted successfully:', result);
      setSuccessMessage('Report submitted successfully! Report ID: ' + result.report_id);

      // Reset form
      setAddress({
        line1: '',
        line2: '',
        city: '',
        state: '',
        zip: '',
        district: '',
      });
      setViolations([{
        id: 1,
        type: '',
        image: null,
        notes: ''
      }]);

    } catch (err) {
      console.error('Submission error:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
      {/* Show error message if there is one */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Show success message if there is one */}
      {successMessage && (
        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {successMessage}
        </div>
      )}

      <div className="mb-8">
        <h2 className="text-lg font-medium text-gray-800 mb-4">
          Location Details
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label
              htmlFor="line1"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Address Line 1
            </label>
            <input
              id="line1"
              type="text"
              value={address.line1}
              onChange={handleAddressChange('line1')}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Street address"
              required
            />
          </div>
          <div className="md:col-span-2">
            <label
              htmlFor="line2"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Address Line 2
            </label>
            <input
              id="line2"
              type="text"
              value={address.line2}
              onChange={handleAddressChange('line2')}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Apartment, suite, unit, etc. (optional)"
            />
          </div>
          <div>
            <label
              htmlFor="city"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              City
            </label>
            <input
              id="city"
              type="text"
              value={address.city}
              onChange={handleAddressChange('city')}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="state"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                State
              </label>
              <input
                id="state"
                type="text"
                value={address.state}
                onChange={handleAddressChange('state')}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label
                htmlFor="zip"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                ZIP Code
              </label>
              <input
                id="zip"
                type="text"
                value={address.zip}
                onChange={handleAddressChange('zip')}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
          </div>
          <div className="md:col-span-2">
            <label
              htmlFor="district"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Metro District
            </label>
            <select
              id="district"
              value={address.district}
              onChange={handleAddressChange('district')}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            >
              {districts.map((district) => (
                <option key={district.value} value={district.value}>
                  {district.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-800 mb-3">Violations</h2>
        {violations.map(violation => (
          <ViolationItem
            key={violation.id}
            violation={violation}
            updateViolation={updateViolation}
            removeViolation={removeViolation}
            showRemoveButton={violations.length > 1}
          />
        ))}
        <button
          type="button"
          onClick={handleAddViolation}
          className="mt-4 flex items-center text-blue-600 hover:text-blue-800"
        >
          <PlusCircleIcon className="w-5 h-5 mr-1" />
          <span>Add another violation</span>
        </button>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className={`px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${isSubmitting
            ? 'bg-blue-400 text-white cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Report'}
        </button>
      </div>
    </form>
  );
}
