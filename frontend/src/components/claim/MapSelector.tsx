import React, { useState } from 'react';
import { MapContainer, TileLayer, useMapEvents, Polygon, Circle } from 'react-leaflet';
import { LatLng } from 'leaflet';
import { motion } from 'framer-motion';
import { MapPin, Square, Circle as CircleIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import 'leaflet/dist/leaflet.css';

interface MapSelectorProps {
  onLocationSelect: (location: { lat: number; lng: number; polygon?: [number, number][] }) => void;
  initialLocation?: { lat: number; lng: number; polygon?: [number, number][] };
}

const MapSelector: React.FC<MapSelectorProps> = ({ onLocationSelect, initialLocation }) => {
  const [selectedPoint, setSelectedPoint] = useState<LatLng | null>(
    initialLocation ? new LatLng(initialLocation.lat, initialLocation.lng) : null
  );
  const [polygon, setPolygon] = useState<[number, number][]>(initialLocation?.polygon || []);
  const [bufferRadius, setBufferRadius] = useState<number>(100); // meters
  const [drawMode, setDrawMode] = useState<'point' | 'buffer' | 'polygon'>('point');

  // Map click handler component
  const MapClickHandler = () => {
    useMapEvents({
      click: (e) => {
        if (drawMode === 'point') {
          setSelectedPoint(e.latlng);
          setPolygon([]);
          
          // Auto-generate buffer polygon
          const bufferPolygon = generateBufferPolygon(e.latlng, bufferRadius);
          setPolygon(bufferPolygon);
          
          onLocationSelect({
            lat: e.latlng.lat,
            lng: e.latlng.lng,
            polygon: bufferPolygon
          });
        }
      }
    });
    return null;
  };

  // Generate circular buffer polygon
  const generateBufferPolygon = (center: LatLng, radius: number): [number, number][] => {
    const points: [number, number][] = [];
    const earthRadius = 6371000; // Earth's radius in meters
    
    for (let i = 0; i < 32; i++) {
      const angle = (i * 360) / 32;
      const angleRad = (angle * Math.PI) / 180;
      
      const lat = center.lat + (radius / earthRadius) * (180 / Math.PI) * Math.cos(angleRad);
      const lng = center.lng + (radius / earthRadius) * (180 / Math.PI) * Math.sin(angleRad) / Math.cos(center.lat * Math.PI / 180);
      
      points.push([lat, lng]);
    }
    
    return points;
  };

  const handleBufferRadiusChange = (newRadius: number) => {
    setBufferRadius(newRadius);
    if (selectedPoint) {
      const bufferPolygon = generateBufferPolygon(selectedPoint, newRadius);
      setPolygon(bufferPolygon);
      onLocationSelect({
        lat: selectedPoint.lat,
        lng: selectedPoint.lng,
        polygon: bufferPolygon
      });
    }
  };

  const calculateArea = (polygon: [number, number][]): number => {
    if (polygon.length < 3) return 0;
    
    // Simple area calculation (approximate for small areas)
    let area = 0;
    for (let i = 0; i < polygon.length; i++) {
      const j = (i + 1) % polygon.length;
      area += polygon[i][0] * polygon[j][1];
      area -= polygon[j][0] * polygon[i][1];
    }
    return Math.abs(area / 2) * 111320 * 111320; // Convert to square meters (approximate)
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MapPin className="h-5 w-5 text-primary-600" />
            <span>Select Project Location</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Drawing Mode Controls */}
          <div className="flex flex-wrap gap-2 mb-4">
            <Button
              variant={drawMode === 'point' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDrawMode('point')}
              className="flex items-center space-x-2"
            >
              <MapPin className="h-4 w-4" />
              <span>Point & Buffer</span>
            </Button>
            <Button
              variant={drawMode === 'buffer' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDrawMode('buffer')}
              className="flex items-center space-x-2"
            >
              <CircleIcon className="h-4 w-4" />
              <span>Circular Area</span>
            </Button>
            <Button
              variant={drawMode === 'polygon' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDrawMode('polygon')}
              className="flex items-center space-x-2"
            >
              <Square className="h-4 w-4" />
              <span>Custom Polygon</span>
            </Button>
          </div>

          {/* Buffer Radius Control */}
          {drawMode === 'point' && (
            <div className="mb-4 p-4 bg-gray-50 rounded-xl">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Buffer Radius: {bufferRadius}m
              </label>
              <input
                type="range"
                min="50"
                max="1000"
                step="50"
                value={bufferRadius}
                onChange={(e) => handleBufferRadiusChange(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>50m</span>
                <span>1000m</span>
              </div>
            </div>
          )}

          {/* Map Container */}
          <div className="h-96 rounded-xl overflow-hidden border border-gray-200">
            <MapContainer
              center={selectedPoint || [40.7128, -74.0060]} // Default to NYC
              zoom={13}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              <MapClickHandler />
              
              {/* Selected Point */}
              {selectedPoint && (
                <Circle
                  center={selectedPoint}
                  radius={5}
                  pathOptions={{ color: '#14532d', fillColor: '#22c55e', fillOpacity: 0.8 }}
                />
              )}
              
              {/* Polygon */}
              {polygon.length > 0 && (
                <Polygon
                  positions={polygon}
                  pathOptions={{
                    color: '#14532d',
                    fillColor: '#22c55e',
                    fillOpacity: 0.3,
                    weight: 2
                  }}
                />
              )}
            </MapContainer>
          </div>

          {/* Location Info */}
          {selectedPoint && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 bg-primary-50 rounded-xl"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium text-primary-900">Coordinates:</span>
                  <div className="text-primary-700">
                    {selectedPoint.lat.toFixed(6)}, {selectedPoint.lng.toFixed(6)}
                  </div>
                </div>
                {polygon.length > 0 && (
                  <div>
                    <span className="font-medium text-primary-900">Area:</span>
                    <div className="text-primary-700">
                      {(calculateArea(polygon) / 10000).toFixed(2)} hectares
                    </div>
                  </div>
                )}
                <div>
                  <span className="font-medium text-primary-900">Status:</span>
                  <div className="text-green-600 font-medium">Location Selected</div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Instructions */}
          <div className="mt-4 text-sm text-gray-600">
            <p className="mb-2">
              <strong>Instructions:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1">
              <li>Click on the map to select your project location</li>
              <li>Adjust the buffer radius to define the project area</li>
              <li>The system will automatically generate a circular boundary</li>
              <li>For custom shapes, use the polygon drawing tool</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default MapSelector;