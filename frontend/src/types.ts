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
  bloodType?: string;
  pediatricianName?: string;
  allergies: string[];
  foodAllergies?: string[];
  medicationAllergies?: string[];
}

export interface NutritionRecommendationItem {
  foodName: string;
  reason: string;
}

export interface NutritionAvoidanceItem {
  foodName: string;
  reason: string;
  linkedTo: string;
}

export interface NutritionRecommendation {
  id: string;
  babyId: string;
  generatedAt: string;
  recommendedFoods: NutritionRecommendationItem[];
  foodsToAvoid: NutritionAvoidanceItem[];
  summary: string;
  basedOnAllergies: string[];
  basedOnConditions: string[];
}

export interface MealSlot {
  mealType: string; // "sáng" | "trưa" | "tối" | "phụ"
  foodName: string;
  note?: string;
}

export interface DayPlan {
  date: string; // YYYY-MM-DD
  meals: MealSlot[];
}

export interface WeeklyMealPlan {
  id: string;
  babyId: string;
  generatedAt: string;
  startDate: string;
  endDate: string;
  status: "pending" | "accepted";
  acceptedAt?: string;
  days: DayPlan[];
  summary: string;
  basedOnAllergies: string[];
  basedOnConditions: string[];
}

export interface FoodSafetyItem {
  name: string;
  reason: string;
  category: string; // "under_1_year" | "choking_hazard"
  minAgeMonths: number;
}

export interface AllergenAlert {
  allergens: string[];
  warningMessage: string;
  hasAlert: boolean;
}

export interface NutritionSafety {
  foodsToAvoid: FoodSafetyItem[];
  allergenAlerts: AllergenAlert;
}

export interface SafetyHandbookSection {
  title: string;
  description: string;
  items?: string[];
  level: string; // "info" | "danger" | "warning" | "success"
}

export interface SafetyHandbook {
  title: string;
  sections: SafetyHandbookSection[];
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

export type MedicationRoute =
  | "Oral (Đường uống)"
  | "Nasal Spray (Xịt mũi)"
  | "Eye/Ear Drops (Nhỏ mắt/tai)"
  | "Topical (Bôi da)"
  | "Inhalation (Khí dung)";

export type MealTiming =
  | "before_food"
  | "after_food"
  | "with_food"
  | "empty_stomach"
  | "anytime"
  | "when_fever";

export type PlanStatus = "active" | "completed" | "paused";

export interface MedicationPlan {
  id: string;
  babyId?: string;
  name: string;
  alternative_name?: string;
  strength?: string;
  dose: string;
  unit: string;
  route: string;
  frequency: string;
  schedule_times: string[];
  meal_timing: string;
  start_date: string;
  end_date?: string;
  duration_days?: number;
  purpose?: string;
  instructions?: string;
  prescribed_by?: string;
  status: PlanStatus;
  created_at?: string;
  updated_at?: string;
}

export interface MedicationDoseLog {
  id?: string;
  baby_id?: string;
  plan_id?: string;
  medication_name: string;
  scheduled_date: string;
  scheduled_time: string;
  taken_at?: string;
  dose_taken: string;
  status: "taken" | "skipped" | "snoozed" | "pending";
  administered_by: string;
  notes?: string;
  created_at?: string;
}

export interface TodayDoseItem {
  dose_id: string;
  plan_id?: string;
  medication_name: string;
  alternative_name?: string;
  strength?: string;
  dose_display: string;
  route: string;
  meal_timing: string;
  scheduled_time: string;
  session: "morning" | "afternoon" | "evening" | "night" | "prn";
  status: "pending" | "taken" | "skipped" | "snoozed";
  taken_at?: string;
  administered_by?: string;
  instructions?: string;
  purpose?: string;
}

export interface MedicationLog {
  id: string;
  babyId: string;
  name: string;
  dosage: string;
  time: string;
  date: string;
  prescribedBy?: string;
  givenBy?: string;
  given_by?: string;
  notes?: string;
}

export interface Guardian {
  id: string;
  name: string;
  email: string;
  role: "ADMIN" | "GUARDIAN" | "VIEWER" | "dad" | "mom" | "grandparent" | string;
  relationship?: string;
  status: "Synced" | "Pending" | "Invited" | string;
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

export interface ToolStep {
  id?: string;
  tool_name: string;
  display_name: string;
  args?: any;
  status: string;
  result_summary?: string;
  start_time?: string;
  duration_ms?: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  extraction?: SmartExtraction | null;
  citations?: Citation[];
  toolSteps?: ToolStep[];
  tool_steps?: ToolStep[];
  activeStepName?: string;
  isVoice?: boolean;
  voiceDuration?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: "medication" | "safety" | "feeding" | "system" | "health_check";
  created_at: string;
  read: boolean;
  action_url?: string;
}
