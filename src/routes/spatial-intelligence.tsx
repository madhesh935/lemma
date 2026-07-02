import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useRef } from "react";
import L from "leaflet";
import { 
  Map as MapIcon, Navigation, Radio, Eye, AlertTriangle, Layers, Activity,
  Filter, Clock, ShieldAlert, Crosshair, ChevronRight, Play, Pause, FastForward,
  MapPin, Route as RouteIcon, Video, Smartphone, User, FileText, LocateFixed, Radar,
  Car, Shield, BrainCircuit, Compass, Zap
} from "lucide-react";
import { Shell } from "@/components/aegis/Shell";
import { StatCard } from "@/components/aegis/StatCard";
import { motion } from "framer-motion";

export const Route = createFileRoute("/spatial-intelligence")({
  component: SpatialIntelligencePage,
});

// Mock Data
const MOCK_HOTSPOTS = [
  { id: 1, lat: 13.0827, lng: 80.2707, label: "Crime Scene Alpha", type: "crime_scene", intensity: 0.95 },
  { id: 2, lat: 13.0950, lng: 80.2500, label: "Suspect Last Seen", type: "cctv", intensity: 0.8 },
  { id: 3, lat: 13.0700, lng: 80.2800, label: "Witness Location", type: "witness", intensity: 0.6 },
  { id: 4, lat: 13.0880, lng: 80.2650, label: "Phone Ping Tower", type: "cdr", intensity: 0.75 },
  { id: 5, lat: 13.0750, lng: 80.2550, label: "GPS Waypoint 1", type: "gps", intensity: 0.9 },
  { id: 6, lat: 13.0650, lng: 80.2450, label: "Vehicle Spotted", type: "vehicle", intensity: 0.85 },
];

const MOCK_MOVEMENT = [
  { time: "06:14", lat: 13.0750, lng: 80.2550, source: "gps", label: "GPS anomaly detected" },
  { time: "07:02", lat: 13.0880, lng: 80.2650, source: "cdr", label: "Vehicle entered geofence" },
  { time: "08:30", lat: 13.0950, lng: 80.2500, source: "cctv", label: "Witness location verified" },
  { time: "09:15", lat: 13.0827, lng: 80.2707, source: "crime_scene", label: "High-risk zone detected" },
  { time: "10:45", lat: 13.0700, lng: 80.2800, source: "vehicle", label: "Movement reconstruction complete" },
];

const SOURCE_COLORS: Record<string, string> = {
  gps: "text-cyan-400",
  cdr: "text-purple-400",
  cctv: "text-orange-400",
  witness: "text-blue-400",
  crime_scene: "text-red-400",
  vehicle: "text-yellow-400",
};

const SOURCE_DOTS: Record<string, string> = {
  gps: "bg-cyan-400", cdr: "bg-purple-400", cctv: "bg-orange-400",
  witness: "bg-blue-400", crime_scene: "bg-red-400", vehicle: "bg-yellow-400",
};

const EVIDENCE_LAYERS = [
  { id: "cctv", label: "CCTV", icon: <Video className="w-3 h-3" /> },
  { id: "gps", label: "GPS", icon: <Navigation className="w-3 h-3" /> },
  { id: "cdr", label: "Mobile Tower", icon: <Smartphone className="w-3 h-3" /> },
  { id: "witness", label: "Witness", icon: <User className="w-3 h-3" /> },
  { id: "autopsy", label: "Autopsy", icon: <FileText className="w-3 h-3" /> },
  { id: "crime_scene", label: "Crime Scene", icon: <AlertTriangle className="w-3 h-3" /> },
  { id: "vehicle", label: "Vehicle Tracking", icon: <RouteIcon className="w-3 h-3" /> },
];

function MapVisualization({ activeLayers }: { activeLayers: string[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.LayerGroup | null>(null);
  const polylineRef = useRef<L.Polyline | null>(null);

  const center: [number, number] = [13.0827, 80.2707]; // Chennai Center

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize map
    const map = L.map(containerRef.current, {
      center: center,
      zoom: 13,
      zoomControl: false,
      attributionControl: false,
    });
    mapRef.current = map;

    // OSM standard tile layer (we will style it via CSS filters globally)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(map);

    // Layer group for dynamic markers
    const markersGroup = L.layerGroup().addTo(map);
    markersRef.current = markersGroup;

    // Polyline for movement path
    const pathCoords = MOCK_MOVEMENT.map(p => [p.lat, p.lng] as [number, number]);
    const polyline = L.polyline(pathCoords, {
      color: "#00C8FF",
      weight: 3,
      opacity: 0.8,
      dashArray: "8, 6",
    }).addTo(map);
    polylineRef.current = polyline;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update visible markers based on activeLayers
  useEffect(() => {
    const map = mapRef.current;
    const markersGroup = markersRef.current;
    if (!map || !markersGroup) return;

    markersGroup.clearLayers();

    const visibleHotspots = MOCK_HOTSPOTS.filter(
      hs => activeLayers.includes(hs.type) || activeLayers.includes("all")
    );

    visibleHotspots.forEach(hs => {
      const color = hs.type === "crime_scene" ? "#FF4D6D" : "#00C8FF";
      
      const m = L.circleMarker([hs.lat, hs.lng], {
        radius: 8,
        color: color,
        fillColor: color,
        fillOpacity: 0.6,
        weight: 2,
      }).addTo(markersGroup);

      m.bindTooltip(
        `<div style="color: #fff; background: #0D1528; border: 1px solid rgba(0,180,255,0.4); padding: 6px 10px; border-radius: 8px; font-size: 11px;">
           <b style="color: ${color}">${hs.label}</b><br/>
           <span style="opacity: 0.6; font-family: monospace;">LAT: ${hs.lat.toFixed(4)} LNG: ${hs.lng.toFixed(4)}</span>
         </div>`,
        { direction: "top", className: "custom-map-tooltip" }
      );
    });
  }, [activeLayers]);

  return (
    <div className="relative w-full h-full rounded-[16px] overflow-hidden border border-[rgba(0,180,255,0.22)]">
      <div ref={containerRef} className="w-full h-full min-h-[400px] z-0" />

      {/* Map UI Overlay Elements */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
        <button 
          onClick={() => mapRef.current?.zoomIn()}
          className="w-10 h-10 rounded-xl bg-[#0D1528]/80 backdrop-blur-md border border-white/10 flex items-center justify-center shadow-[0_0_10px_rgba(0,180,255,0.05)] cursor-pointer hover:bg-white/[0.05] transition-all text-[#00C8FF] text-lg font-bold hover:scale-105"
        >
          +
        </button>
        <button 
          onClick={() => mapRef.current?.zoomOut()}
          className="w-10 h-10 rounded-xl bg-[#0D1528]/80 backdrop-blur-md border border-white/10 flex items-center justify-center shadow-[0_0_10px_rgba(0,180,255,0.05)] cursor-pointer hover:bg-white/[0.05] transition-all text-[#00C8FF] text-lg font-bold hover:scale-105"
        >
          -
        </button>
      </div>
      
      <div className="absolute bottom-4 left-4 z-[1000]">
        <div className="bg-[#0D1528]/80 backdrop-blur-md border border-white/10 px-3 py-1.5 rounded-lg flex items-center gap-2 shadow-[0_0_10px_rgba(0,180,255,0.05)]">
          <Radar className="w-3.5 h-3.5 text-[#00D084] animate-pulse" />
          <span className="text-[10px] font-mono font-semibold tracking-wider text-[#00D084]">SAT-LINK SECURE · 47.92 MS</span>
        </div>
      </div>
    </div>
  );
}

function LiveSpatialFeed() {
  return (
    <div className="h-full flex flex-col space-y-4">
      {MOCK_MOVEMENT.map((evt, i) => (
        <motion.div 
          key={i} 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1 }}
          className="flex items-start gap-4 p-4 rounded-[14px] bg-[#070B17] border border-white/5 hover:border-[rgba(0,180,255,0.3)] transition-all group cursor-pointer"
        >
          <div className="flex flex-col items-center gap-1.5 mt-1">
            <span className={`w-2 h-2 rounded-full shadow-[0_0_5px_currentColor] ${SOURCE_DOTS[evt.source]}`} />
            <div className="w-px h-10 bg-white/10 group-last:hidden" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <span className={`text-[10px] font-bold uppercase tracking-wider ${SOURCE_COLORS[evt.source]}`}>{evt.source} Event</span>
              <span className="text-[10px] font-mono text-white/30">{evt.time}</span>
            </div>
            <div className="text-sm font-medium text-white/90 mb-1.5">{evt.label}</div>
            <div className="text-[10px] font-mono text-white/40 flex gap-3">
              <span>LAT: {evt.lat.toFixed(4)}</span>
              <span>LNG: {evt.lng.toFixed(4)}</span>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function SpatialIntelligencePage() {
  const [activeLayers, setActiveLayers] = useState<string[]>(["all", "crime_scene", "gps", "cctv", "cdr"]);
  const [isPlaying, setIsPlaying] = useState(false);

  const toggleLayer = (id: string) => {
    setActiveLayers(prev => 
      prev.includes(id) ? prev.filter(l => l !== id) : [...prev, id]
    );
  };

  return (
    <Shell>
      <div className="max-w-[1600px] mx-auto p-8 space-y-6 text-white font-sans">
        
        {/* Header */}
        <div className="flex flex-col items-start mb-2">
          <div className="flex items-center gap-2 mb-3">
            <MapIcon className="w-4 h-4 text-[#00C8FF]" />
            <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider">GEOINT ANALYSIS</h2>
            <span className="text-xs text-white/20 ml-auto flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00D084] animate-pulse" />
              Real-time Feed Active
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-1">
            Spatial Intelligence
          </h1>
          <p className="text-sm text-white/50 max-w-4xl">
            Real-time geospatial intelligence powered by AI for crime hotspot detection, suspect movement reconstruction, GPS correlation and predictive policing.
          </p>
        </div>

        {/* TOP: Dashboard Metrics (6 cards) */}
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
          <StatCard label="Crime Hotspots" value={14} icon={MapPin} tone="danger" sub="identified" trend="↑ 2 active" />
          <StatCard label="Tracked Vehicles" value={8} icon={Car} tone="warn" sub="suspect plates" trend="3 moving" />
          <StatCard label="GPS Trails" value={102} icon={RouteIcon} tone="neon-2" sub="waypoints" trend="correlated" />
          <StatCard label="Active Geofences" value={3} icon={Shield} tone="success" sub="zones secured" trend="0 breaches" />
          <StatCard label="Movement Alerts" value={27} icon={Activity} tone="neon-2" sub="today" trend="AI verified" />
          <StatCard label="Prediction Conf" value={92} icon={BrainCircuit} tone="success" sub="percent" trend="high accuracy" />
        </div>

        {/* CENTER: Map & Right Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[500px]">
          
          {/* Main Map Area */}
          <div className="lg:col-span-8 flex flex-col gap-4">
            <div className="bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-2 h-full flex flex-col relative shadow-[0_0_15px_rgba(0,180,255,0.05)]">
              <div className="flex-1 relative min-h-[400px]">
                <MapVisualization activeLayers={activeLayers} />
              </div>

              {/* Bottom Controls inside Map Card */}
              <div className="mt-4 px-4 pb-2 space-y-4">
                {/* Layer Toggles */}
                <div className="flex items-center gap-4">
                  <div className="text-[10px] text-white/50 uppercase tracking-widest font-bold whitespace-nowrap">Evidence Layers</div>
                  <div className="flex flex-wrap gap-2">
                    {EVIDENCE_LAYERS.map(layer => {
                      const isActive = activeLayers.includes(layer.id) || activeLayers.includes("all");
                      return (
                        <button
                          key={layer.id}
                          onClick={() => toggleLayer(layer.id)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all text-[11px] font-medium
                            ${isActive 
                              ? `bg-white/[0.05] border-[rgba(0,180,255,0.4)] text-[#00C8FF] shadow-[0_0_10px_rgba(0,180,255,0.1)]` 
                              : 'bg-[#070B17] border-white/5 text-white/40 hover:bg-white/[0.02] hover:text-white/70'
                            }`}
                        >
                          {layer.icon} {layer.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Timeline Slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="text-[10px] text-white/50 uppercase tracking-widest font-bold">Movement Replay</div>
                    </div>
                    <div className="flex gap-1.5">
                      <button onClick={() => setIsPlaying(!isPlaying)} className="p-1.5 rounded-md bg-[#00C8FF]/10 text-[#00C8FF] hover:bg-[#00C8FF]/20 transition-colors">
                        {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                      </button>
                      <button className="p-1.5 rounded-md bg-white/5 text-white/50 hover:bg-white/10 hover:text-white transition-colors">
                        <FastForward className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="h-1.5 bg-[#070B17] rounded-full overflow-hidden relative cursor-pointer group border border-white/5">
                    <div className="absolute top-0 left-0 h-full bg-[#00C8FF] w-[60%] shadow-[0_0_10px_#00C8FF]" />
                    <div className="absolute top-1/2 -mt-1 w-2 h-2 bg-white rounded-full left-[60%] shadow-[0_0_10px_#ffffff] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div className="flex justify-between text-[9px] text-white/30 font-mono mt-1.5">
                    <span>00:00 HRS</span>
                    <span className="text-[#00C8FF]">08:30 HRS (CURRENT)</span>
                    <span>24:00 HRS</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel: Live Spatial Feed */}
          <div className="lg:col-span-4 bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-5 flex flex-col shadow-[0_0_15px_rgba(0,180,255,0.05)]">
            <h3 className="text-xs font-bold text-white/70 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#00C8FF]" /> Live Spatial Feed
            </h3>
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
              <LiveSpatialFeed />
            </div>
          </div>

        </div>

        {/* BOTTOM: Three Glass Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-5 shadow-[0_0_15px_rgba(0,180,255,0.05)] hover:border-[rgba(0,180,255,0.4)] transition-all">
            <h3 className="text-xs font-bold text-[#00C8FF] uppercase tracking-widest mb-4 flex items-center gap-2">
              <RouteIcon className="w-4 h-4" /> Movement Intelligence
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Confidence Score</span>
                <span className="text-sm font-bold text-[#00D084]">94%</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Average Travel Time</span>
                <span className="text-sm font-bold text-white">42 mins</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Known Stops</span>
                <span className="text-sm font-bold text-white">3</span>
              </div>
              <div className="flex justify-between items-center pb-1">
                <span className="text-sm text-white/60">Pattern Match</span>
                <span className="text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded text-white/80 border border-white/10">MODUS-OPERANDI-ALPHA</span>
              </div>
            </div>
          </div>

          <div className="bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-5 shadow-[0_0_15px_rgba(0,180,255,0.05)] hover:border-[rgba(0,180,255,0.4)] transition-all">
            <h3 className="text-xs font-bold text-[#00C8FF] uppercase tracking-widest mb-4 flex items-center gap-2">
              <MapPin className="w-4 h-4" /> Hotspot Analytics
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">High Risk Zones</span>
                <span className="text-sm font-bold text-[#FF4D6D]">2 Detected</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Crime Density</span>
                <span className="text-sm font-bold text-[#FFC857]">Elevated</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Prediction Score</span>
                <span className="text-sm font-bold text-[#00D084]">88%</span>
              </div>
              <div className="flex justify-between items-center pb-1">
                <span className="text-sm text-white/60">AI Summary</span>
                <span className="text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded text-white/80 border border-white/10">ESCALATION_LIKELY</span>
              </div>
            </div>
          </div>

          <div className="bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-5 shadow-[0_0_15px_rgba(0,180,255,0.05)] hover:border-[rgba(0,180,255,0.4)] transition-all">
            <h3 className="text-xs font-bold text-[#00C8FF] uppercase tracking-widest mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4" /> Geofence Intelligence
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Restricted Areas</span>
                <span className="text-sm font-bold text-white">4 Active</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Evidence Radius</span>
                <span className="text-sm font-bold text-white">5.2 km</span>
              </div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <span className="text-sm text-white/60">Entry Alerts</span>
                <span className="text-sm font-bold text-[#FFC857]">12 Today</span>
              </div>
              <div className="flex justify-between items-center pb-1">
                <span className="text-sm text-white/60">Zone Timeline</span>
                <span className="text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded text-white/80 border border-white/10">SYNCHRONIZED</span>
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM ROW: AI Insights Banner */}
        <div className="bg-gradient-to-r from-[#00C8FF]/10 to-transparent border border-[#00C8FF]/30 rounded-[18px] p-4 flex items-center justify-between shadow-[0_0_20px_rgba(0,200,255,0.1)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#00C8FF]/20 flex items-center justify-center border border-[#00C8FF]/50">
              <Zap className="w-5 h-5 text-[#00C8FF]" />
            </div>
            <div>
              <div className="text-sm font-bold text-white">Lemma Spatial AI Insight</div>
              <div className="text-xs text-white/60">Suspect movement pattern strongly correlates with historical burglary hotspots in Sector 4. Recommend dispatching patrol unit to Waypoint Alpha.</div>
            </div>
          </div>
          <button className="px-4 py-2 bg-[#00C8FF]/20 hover:bg-[#00C8FF]/30 text-[#00C8FF] text-xs font-bold uppercase tracking-wider rounded-lg border border-[#00C8FF]/40 transition-colors">
            Deploy Units
          </button>
        </div>

      </div>
    </Shell>
  );
}
