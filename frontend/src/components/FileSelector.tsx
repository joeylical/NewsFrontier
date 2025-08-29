'use client';

import React, { useRef } from 'react';
import { FileText, Upload } from 'lucide-react';

interface FileSelectorProps {
  onFileSelect: (content: string, fileName: string) => void;
  acceptedTypes?: string[];
  className?: string;
  disabled?: boolean;
}

const FileSelector: React.FC<FileSelectorProps> = ({
  onFileSelect,
  acceptedTypes = ['.yaml', '.yml', '.txt'],
  className = '',
  disabled = false
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      
      // Validate file type
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedTypes.includes(fileExt)) {
        alert(`Invalid file type. Accepted types: ${acceptedTypes.join(', ')}`);
        return;
      }

      try {
        const content = await file.text();
        
        // If it's a TXT file, convert to YAML format
        if (fileExt === '.txt') {
          const promptName = file.name.replace('.txt', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          const yamlContent = `name: ${promptName}
description: Imported from ${file.name}
stages:
  - name: main_prompt
    type: final
    prompt: |
${content.split('\n').map(line => '      ' + line).join('\n')}
    llm_params:
      temperature: 0.7
      max_tokens: 1000`;
          
          onFileSelect(yamlContent, file.name);
        } else {
          // YAML file - use content as-is
          onFileSelect(content, file.name);
        }
      } catch (error) {
        alert('Error reading file: ' + (error instanceof Error ? error.message : 'Unknown error'));
      }
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const triggerFileSelect = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className={className}>
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes.join(',')}
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled}
      />
      
      <button
        onClick={triggerFileSelect}
        disabled={disabled}
        className={`inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed ${disabled ? '' : 'hover:border-gray-400'}`}
      >
        <FileText className="w-4 h-4 mr-2" />
        Load from File
      </button>
      
      <div className="text-xs text-gray-500 mt-1">
        Supports: {acceptedTypes.join(', ')} files
      </div>
    </div>
  );
};

export default FileSelector;