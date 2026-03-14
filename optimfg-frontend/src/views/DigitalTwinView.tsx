import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Environment, ContactShadows, Float } from '@react-three/drei';
import * as THREE from 'three';
import { Activity, AlertTriangle, CheckCircle2 } from 'lucide-react';

// --- Sub-components for the 3D Scene ---

function ReactorCore({ isOverheating }: { isOverheating: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.5;
    }
  });

  const coreColor = isOverheating ? '#ef4444' : '#3b82f6';
  const emissiveIntensity = isOverheating ? 2.5 : 0.8;

  return (
    <group position={[0, 1.5, 0]}>
      {/* Reactor Body */}
      <mesh ref={meshRef}>
        <cylinderGeometry args={[1.5, 1.5, 3, 32]} />
        <meshStandardMaterial 
          color="#e2e8f0" 
          metalness={0.8} 
          roughness={0.2} 
        />
      </mesh>
      
      {/* Glowing Inner Core Ring */}
      <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.55, 0.1, 16, 100]} />
        <meshStandardMaterial 
          color={coreColor} 
          emissive={coreColor} 
          emissiveIntensity={emissiveIntensity}
        />
      </mesh>

      {/* Pipes */}
      <mesh position={[-1.6, 1, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.2, 0.2, 1, 16]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.6} roughness={0.4} />
      </mesh>
      <mesh position={[1.6, -1, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.2, 0.2, 1, 16]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.6} roughness={0.4} />
      </mesh>
    </group>
  );
}

function DataOverlay({ 
  position, 
  title, 
  value, 
  unit, 
  status = 'normal' 
}: { 
  position: [number, number, number]; 
  title: string; 
  value: string | number; 
  unit: string;
  status?: 'normal' | 'warning' | 'critical';
}) {
  const getStatusColor = () => {
    switch (status) {
      case 'critical': return 'text-red-500';
      case 'warning': return 'text-amber-500';
      default: return 'text-emerald-500';
    }
  };

  const StatusIcon = status === 'critical' ? AlertTriangle : status === 'warning' ? AlertTriangle : CheckCircle2;

  // Uses vanilla CSS classes where possible, matching the app's clean white theme
  return (
    <Html position={position} center distanceFactor={15}>
      <div 
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(0, 0, 0, 0.05)',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
          borderRadius: '12px',
          padding: '12px 16px',
          width: 'max-content',
          minWidth: '160px',
          pointerEvents: 'none',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {title}
          </span>
          <StatusIcon size={14} className={getStatusColor()} style={{ color: status === 'critical' ? '#ef4444' : status === 'warning' ? '#f59e0b' : '#10b981' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
          <span style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', lineHeight: 1 }}>{value}</span>
          <span style={{ fontSize: '14px', fontWeight: 500, color: '#64748b' }}>{unit}</span>
        </div>
      </div>
    </Html>
  );
}

function Scene({ simulatedData }: { simulatedData: any }) {
  const isOverheating = simulatedData.temperature > 500;

  return (
    <>
      <Environment preset="city" />
      <ambientLight intensity={0.5} />
      <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
      
      <Float speed={2} rotationIntensity={0.1} floatIntensity={0.2}>
        <ReactorCore isOverheating={isOverheating} />
        
        {/* Sensor Data Anchors */}
        <DataOverlay 
          position={[2.2, 2.5, 0]} 
          title="Core Temperature" 
          value={simulatedData.temperature} 
          unit="°C" 
          status={isOverheating ? 'critical' : 'normal'}
        />
        
        <DataOverlay 
          position={[-2.2, 1, 0]} 
          title="Inlet Pressure" 
          value={simulatedData.pressure} 
          unit="atm" 
          status={simulatedData.pressure > 2.5 ? 'warning' : 'normal'}
        />

        <DataOverlay 
          position={[0, -0.5, 2]} 
          title="Yield Efficiency" 
          value={simulatedData.yield} 
          unit="%" 
          status={simulatedData.yield < 80 ? 'warning' : 'normal'}
        />
      </Float>

      <ContactShadows position={[0, -1.5, 0]} opacity={0.4} scale={10} blur={2} far={4} />
      <OrbitControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 1.5} />
    </>
  );
}

// --- Main View Component ---

export default function DigitalTwinView() {
  // Mock live data state
  const [data, setData] = useState({
    temperature: 450,
    pressure: 2.1,
    yield: 92.4,
  });

  // Simulate incoming live data
  React.useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => ({
        temperature: Math.round(prev.temperature + (Math.random() * 10 - 5)),
        pressure: Number((prev.pressure + (Math.random() * 0.2 - 0.1)).toFixed(2)),
        yield: Number(Math.min(99.9, prev.yield + (Math.random() * 1 - 0.3)).toFixed(1)),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text)', margin: '0 0 8px 0' }}>Live Digital Twin</h2>
          <p style={{ color: 'var(--text-light)', margin: 0 }}>Real-time 3D spatial visualization of Reactor Unit A-1.</p>
        </div>
        
        <div className="card" style={{ padding: '16px', display: 'flex', gap: '24px', width: 'auto' }}>
           <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
             <span style={{ fontSize: '12px', color: 'var(--text-light)', fontWeight: 500 }}>CONNECTION</span>
             <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
               <span className="status-dot" style={{ background: 'var(--success)', animation: 'pulse 2s infinite' }}></span>
               <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>WebSocket Active</span>
             </div>
           </div>
           <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
             <span style={{ fontSize: '12px', color: 'var(--text-light)', fontWeight: 500 }}>LATENCY</span>
             <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>14ms</span>
           </div>
        </div>
      </div>

      <div 
        className="card" 
        style={{ 
          flex: 1, 
          position: 'relative', 
          overflow: 'hidden', 
          padding: 0,
          background: 'linear-gradient(to bottom, #f8fafc, #f1f5f9)' 
        }}
      >
        <div 
          style={{ 
            position: 'absolute', 
            top: 20, 
            left: 20, 
            zIndex: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'white',
            padding: '8px 12px',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
          }}
        >
          <Activity size={16} color="var(--primary)" />
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>Simulation Mode: Auto</span>
        </div>
        
        <div style={{ position: 'absolute', bottom: 20, left: 20, zIndex: 10 }}>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>Left click to rotate • Scroll to zoom • Right click to pan</span>
        </div>

        <Canvas camera={{ position: [5, 3, 5], fov: 50 }} shadows>
          <Scene simulatedData={data} />
        </Canvas>
      </div>
    </div>
  );
}
