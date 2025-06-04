import {
  MessageCircle,
  Users,
  ShieldCheck,
  Lightbulb,
  Repeat,
  Sparkles,
  Brain,
  HelpCircle,
  LucideIcon,
} from 'lucide-react';
import type { SoftSkill } from '@/lib/types';

interface SkillIconProps {
  skill: SoftSkill | string; // Allow string for flexibility if skill names vary
  className?: string;
}

const SKILL_ICON_MAP: Record<SoftSkill, LucideIcon> = {
  'Communication': MessageCircle,
  'Collaboration / Teamwork': Users,
  'Accountability / Ownership': ShieldCheck,
  'Problem-Solving': Lightbulb,
  'Adaptability / Resilience': Repeat,
  'Initiative': Sparkles,
  'Emotional Intelligence (EQ)': Brain,
};

export default function SkillIcon({ skill, className }: SkillIconProps) {
  const IconComponent = SKILL_ICON_MAP[skill as SoftSkill] || HelpCircle;
  return <IconComponent className={className} />;
}
