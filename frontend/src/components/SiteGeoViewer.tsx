import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';
import React from 'react';

const MapComponent = dynamic(
  () => import('./MapComponent'),
  { 
    ssr: false,
    loading: () => (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 h-[500px] flex flex-col items-center justify-center">
        <Loader2 className="animate-spin text-emerald-500 h-10 w-10 mb-4" />
        <p className="text-gray-500 font-medium">Loading geospatial data layers...</p>
      </div>
    )
  }
);

interface Props {
  data: any;
}

export const SiteGeoViewer: React.FC<Props> = ({ data }) => {
  if (!data) return null;
  return <MapComponent data={data} />;
};
