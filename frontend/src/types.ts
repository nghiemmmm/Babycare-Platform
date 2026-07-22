export enum Gender {
  Boy = "Boy",
  Girl = "Girl",
  Unknown = "Unknown"
}

export interface BabyProfile {
  id: string;
  name: string;
  birthDate: string;
  gender: Gender;
  avatarUrl?: string;
  isActive: boolean;
}

export interface Measurement {
  id: string;
  babyId: string;
  date: string;
  ageInMonths: number;
  weight: number; // kg
  height: number; // cm
  headCircumference: number; // cm
  status: string; // e.g. "Normal", "Height Alert (Risk of Stunting)"
  notes?: string;
}

export interface MedicationLog {
  id: string;
  babyId: string;
  name: string;
  dosage: string;
  time: string;
  date: string;
  prescribedBy?: string;
}

export interface Guardian {
  id: string;
  name: string;
  email: string;
  role: "ADMIN" | "GUARDIAN" | "VIEWER";
  status: "Synced" | "Pending" | "Invited";
}

export interface FeedLog {
  id: string;
  babyId: string;
  type: "Formula" | "Breast" | "Solids";
  details: string; // e.g. "Sweet Potato Purée"
  amount: number; // ml for formula/breast, or meals count for solids
  time: string;
  date: string;
}

export interface IngredientLog {
  id: string;
  babyId: string;
  name: string;
  reaction: "Loved it" | "Spat out" | "Neutral" | "Allergic Reaction";
  date: string;
}

export interface SmartExtraction {
  type: "feeding" | "sleep" | "medication" | "nutrition";
  title: string;
  detail: string;
  value: any;
  time: string;
  pending?: boolean;
}

export interface Citation {
  title: string;
  uri: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  extraction?: SmartExtraction | null;
  citations?: Citation[];
  isVoice?: boolean;
  voiceDuration?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: "medication" | "safety" | "feeding" | "system";
  created_at: string;
  read: boolean;
  action_url?: string;
}
