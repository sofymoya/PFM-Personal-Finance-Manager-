import React from 'react';

interface InputProps {
  type?: string;
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  icon?: React.ReactNode;
  className?: string;
}

const Input: React.FC<InputProps> = ({
  type = 'text',
  label,
  placeholder,
  value,
  onChange,
  required = false,
  disabled = false,
  error,
  icon,
  className = ''
}) => {
  const baseClasses = 'w-full px-4 py-3 border border-neutral-300 rounded-md text-sm transition-all duration-200 ease-in-out bg-white';
  const focusClasses = 'focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-100';
  const disabledClasses = disabled ? 'bg-neutral-100 cursor-not-allowed' : '';
  const errorClasses = error ? 'border-error-500 focus:border-error-500 focus:ring-error-100' : '';

  const inputClasses = [
    baseClasses,
    focusClasses,
    disabledClasses,
    errorClasses,
    className
  ].filter(Boolean).join(' ');

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-neutral-700">
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <div className="text-neutral-400">
              {icon}
            </div>
          </div>
        )}
        
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          required={required}
          disabled={disabled}
          className={`${inputClasses} ${icon ? 'pl-10' : ''}`}
        />
      </div>
      
      {error && (
        <p className="text-sm text-error-600">
          {error}
        </p>
      )}
    </div>
  );
};

export default Input; 