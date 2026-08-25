"use client";
import React, { useState } from "react";
import { UploadCloud } from "lucide-react";

interface Props {
  onUpload?: (files: File[]) => void;
}

export function TenderUploader({ onUpload }: Props) {
  const [files, setFiles] = useState<File[]>([]);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setFiles(Array.from(e.dataTransfer.files));
    }
  };
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };
  const submit = () => {
    if (onUpload) onUpload(files);
  };

  return (
    <div className="w-full text-center">
      <div className="w-full p-8 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 transition hover:bg-gray-100"
           onDragOver={(e) => e.preventDefault()}
           onDrop={handleDrop}>
        <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-semibold text-gray-900">Upload Tender Documents</h3>
        <div className="mt-4">
          <label htmlFor="file-upload" className="cursor-pointer bg-white border px-4 py-2 rounded-md hover:bg-gray-50 text-sm">
            Select Files
          </label>
          <input id="file-upload" type="file" multiple className="hidden" onChange={handleChange} />
        </div>
        {files.length > 0 && (
          <ul className="mt-4 text-left text-sm text-gray-700 bg-white p-2 rounded shadow-sm">
            {files.map((file, i) => <li key={i}>{file.name}</li>)}
          </ul>
        )}
      </div>
      <button 
        onClick={submit} 
        disabled={files.length === 0}
        className="mt-4 w-full bg-blue-600 disabled:bg-gray-400 text-white font-semibold py-3 rounded-md shadow hover:bg-blue-700 transition"
      >
        Run Full-Stack Audit Now
      </button>
    </div>
  );
}
