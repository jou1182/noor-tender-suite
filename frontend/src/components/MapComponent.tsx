import React from 'react';
import { MapContainer, TileLayer, Polyline, Polygon, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, AlertTriangle } from 'lucide-react';

export default function MapComponent({ data }: any) {
  // Use Next.js leaflet dynamic fixes (fixing icon issues)
  React.useEffect(() => {
    const L = require('leaflet');
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    });
  }, []);

  const center = [24.7136, 46.6753] as [number, number];
  
  const projectLine = [
    [24.7136, 46.6753],
    [24.7200, 46.6800]
  ] as [number, number][];

  const hazardZone = [
    [24.7150, 46.6700],
    [24.7250, 46.6700],
    [24.7250, 46.6900],
    [24.7150, 46.6900]
  ] as [number, number][];
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500">
      <h3 className="text-xl font-bold text-gray-800 flex items-center mb-6">
        <MapPin className="mr-2 text-emerald-600" />
        GIS & Geotechnical Site Context
      </h3>
      
      {data.geotech_alerts && data.geotech_alerts.length > 0 && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800 shadow-inner">
          <strong className="flex items-center mb-2"><AlertTriangle size={18} className="mr-2 text-red-600" /> Geotechnical Hazard Alerts:</strong> 
          <ul className="list-disc pl-8 space-y-1 font-medium">
            {data.geotech_alerts.map((a: string, i: number) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}
      
      <div className="h-96 rounded-lg overflow-hidden border border-gray-300 shadow-sm relative z-0">
        <MapContainer center={center} zoom={14} style={{ height: '100%', width: '100%' }}>
          <TileLayer 
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" 
          />
          <Polyline positions={projectLine} color="#2563eb" weight={6}>
            <Popup>Project Alignment (Length: {data.total_length_m}m)</Popup>
          </Polyline>
          <Polygon positions={hazardZone} color="#dc2626" fillColor="#dc2626" fillOpacity={0.2} weight={2}>
            <Popup>High Groundwater Hazard Zone</Popup>
          </Polygon>
        </MapContainer>
      </div>
    </div>
  );
}
