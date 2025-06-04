import React, { useState, useEffect } from 'react';
import { TrashIcon, ImageIcon } from 'lucide-react';

type Violation = {
  id: number;
  type: string;
  image: File | null;
  notes: string;
};

type ViolationItemProps = {
  violation: Violation;
  updateViolation: (id: number, updates: Partial<Violation>) => void;
  removeViolation: (id: number) => void;
  showRemoveButton: boolean;
};

export function ViolationItem({
  violation,
  updateViolation,
  removeViolation,
  showRemoveButton,
}: ViolationItemProps) {
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  useEffect(() => {
    if (violation.image) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(violation.image);
    } else {
      setImagePreview(null);
    }
  }, [violation.image]);

  const violationTypes = [
    { value: '', label: 'Select violation type' },
    { value: 'weeds', label: 'Weeds' },
    { value: 'rv', label: 'RV Parking' },
    { value: 'grass', label: 'Uncut Grass' },
    { value: 'trash', label: 'Trash Cans' },
    { value: 'debris', label: 'Debris' },
    { value: 'structure', label: 'Structure Violation' },
    { value: 'bball_hoop', label: 'Basketball Hoop' },
    { value: 'fence', label: 'Fence Violation' },
    { value: 'other', label: 'Other' },
  ];

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    updateViolation(violation.id, { image: file });
  };

  return (
    <div className="mb-6 p-4 border border-gray-200 rounded-md bg-gray-50">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Violation Type
          </label>
          <select
            value={violation.type}
            onChange={(e) => updateViolation(violation.id, { type: e.target.value })}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            required
          >
            {violationTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
        {showRemoveButton && (
          <button
            type="button"
            onClick={() => removeViolation(violation.id)}
            className="ml-2 text-red-500 hover:text-red-700"
            aria-label="Remove violation"
          >
            <TrashIcon className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Image
        </label>
        <div className="flex items-center">
          <label className="cursor-pointer flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-md hover:bg-gray-100">
            {imagePreview ? (
              <img
                src={imagePreview}
                alt="Violation preview"
                className="max-h-full max-w-full object-contain"
              />
            ) : (
              <div className="text-center">
                <ImageIcon className="mx-auto h-12 w-12 text-gray-400" />
                <span className="mt-2 block text-sm text-gray-600">
                  Take photo or upload
                </span>
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleImageChange}
            />
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={violation.notes}
          onChange={(e) => updateViolation(violation.id, { notes: e.target.value })}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          rows={3}
          placeholder="Add details about this violation"
        />
      </div>
    </div>
  );
}