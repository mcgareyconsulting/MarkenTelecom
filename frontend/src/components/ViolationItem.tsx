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

  // Predefined list of violation types
  const violationTypes = [
    { value: '', label: 'Select violation type' },
    { value: 'address_sign', label: 'Address Sign' },
    { value: 'artificial_plantings', label: 'Artificial Plantings' },
    { value: 'basketball_backboards', label: 'Basketball Backboards' },
    { value: 'decks', label: 'Decks' },
    { value: 'drainage', label: 'Drainage' },
    { value: 'drains', label: 'Drains' },
    { value: 'exterior_lighting', label: 'Exterior Lighting' },
    { value: 'exterior_mechanical_equipment', label: 'Exterior Mechanical Equipment' },
    { value: 'exterior_painting', label: 'Exterior Painting' },
    { value: 'exterior_shutters', label: 'Exterior Shutters' },
    { value: 'exterior_stairs', label: 'Exterior Stairs' },
    { value: 'fences', label: 'Fences' },
    { value: 'flag_poles', label: 'Flag Poles' },
    { value: 'garden_art_front_yard', label: 'Garden Art - Front Yard' },
    { value: 'garden_window', label: 'Garden Window' },
    { value: 'ground_garden_level_decks', label: 'Ground & Garden Level Decks' },
    { value: 'heights_maximum', label: 'Heights - Maximum' },
    { value: 'holiday_lighting', label: 'Holiday Lighting' },
    { value: 'irrigation', label: 'Irrigation' },
    { value: 'lamp_posts', label: 'Lamp Posts' },
    { value: 'patios', label: 'Patios' },
    { value: 'pet_enclosures', label: 'Pet Enclosuers' },
    { value: 'play_equipment', label: 'Play Equipment' },
    { value: 'pools_and_spas', label: 'Pools and Spas' },
    { value: 'ramps_handicap', label: 'Ramps - Handicap' },
    { value: 'satellite_dishes_tennae', label: 'Satellite Dishes / Antennae' },
    { value: 'screen_orm_doors', label: 'Screen / Storm Doors' },
    { value: 'solar_energy_systems', label: 'Solar Energy Systems' },
    { value: 'accesory_structures', label: 'Accesory Structures' },
    { value: 'trash_recycle_cans', label: 'Trash / Recycle Cans' },
    { value: 'unsightly_items', label: 'Unsightly Items' },
    { value: 'walls', label: 'Walls' },
    { value: 'window_awnings', label: 'Window Awnings' },
    { value: 'window_coverings', label: 'Window Coverings' },
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