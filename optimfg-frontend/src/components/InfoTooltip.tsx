import { Info } from 'lucide-react';

interface InfoTooltipProps {
  text: string;
}

export default function InfoTooltip({ text }: InfoTooltipProps) {
  return (
    <div className="info-icon-wrap">
      <Info size={14} />
      <div className="info-tooltip">{text}</div>
    </div>
  );
}
