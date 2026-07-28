import { BabyProfile, Gender, Measurement, MedicationLog, Guardian, FeedLog, IngredientLog, ChatMessage } from "./types";

export const INITIAL_BABIES: BabyProfile[] = [
  {
    id: "baby-leo",
    name: "Leo",
    birthDate: "2023-04-20",
    gender: Gender.Boy,
    avatarUrl: "/static/img/leo.png",
    isActive: true
  },
  {
    id: "baby-bo",
    name: "Bo",
    birthDate: "2023-11-15",
    gender: Gender.Girl,
    avatarUrl: "/static/img/bo.png",
    isActive: false
  }
];

export const INITIAL_MEASUREMENTS: Measurement[] = [
  {
    id: "m1",
    babyId: "baby-leo",
    date: "2023-10-24",
    ageInMonths: 6,
    weight: 7.2,
    height: 66,
    headCircumference: 42.5,
    status: "Height Alert (Risk of Stunting)",
    notes: "Leo is tracking slightly under the WHO median for height (below 15th percentile), but head and weight curves are normal. Pediatrician suggests monitoring calcium and ensuring active outdoor tummy time."
  },
  {
    id: "m2",
    babyId: "baby-leo",
    date: "2023-09-20",
    ageInMonths: 5,
    weight: 6.8,
    height: 64,
    headCircumference: 41.8,
    status: "Normal",
    notes: "Perfect linear progression. Slept well prior to checkup."
  },
  {
    id: "m3",
    babyId: "baby-leo",
    date: "2023-08-15",
    ageInMonths: 4,
    weight: 6.3,
    height: 62.5,
    headCircumference: 41.0,
    status: "Normal",
    notes: "Weight gain is solid, pediatrician pleased."
  }
];

export const INITIAL_MEDICATIONS: MedicationLog[] = [
  {
    id: "med1",
    babyId: "baby-leo",
    name: "Hapacol 150mg (Paracetamol)",
    dosage: "150mg",
    time: "11:45 AM",
    date: "Today",
    prescribedBy: "Dr. Aris"
  },
  {
    id: "med2",
    babyId: "baby-leo",
    name: "Vitamin D3 K2",
    dosage: "2 drops",
    time: "08:00 AM",
    date: "Today",
    prescribedBy: "Daily Supplement"
  },
  {
    id: "med3",
    babyId: "baby-leo",
    name: "Hapacol 150mg (Paracetamol)",
    dosage: "150mg",
    time: "11:30 PM",
    date: "Yesterday",
    prescribedBy: "Dr. Aris"
  }
];

export const INITIAL_GUARDIANS: Guardian[] = [
  {
    id: "g1",
    name: "Alex (Dad)",
    email: "alex.parent@care.com",
    role: "ADMIN",
    status: "Synced"
  },
  {
    id: "g2",
    name: "Nanny Maria",
    email: "maria.nanny@helper.net",
    role: "GUARDIAN",
    status: "Synced"
  },
  {
    id: "g3",
    name: "Grandma Elena",
    email: "elena.grandma@family.org",
    role: "VIEWER",
    status: "Invited"
  }
];

export const INITIAL_FEEDS: FeedLog[] = [
  {
    id: "feed1",
    babyId: "baby-leo",
    type: "Formula",
    details: "180ml Formula",
    amount: 180,
    time: "01:00 PM",
    date: "Today"
  },
  {
    id: "feed2",
    babyId: "baby-leo",
    type: "Solids",
    details: "Sweet Potato Purée",
    amount: 1, // 1 meal
    time: "10:30 AM",
    date: "Today"
  },
  {
    id: "feed3",
    babyId: "baby-leo",
    type: "Formula",
    details: "180ml Formula",
    amount: 180,
    time: "08:00 AM",
    date: "Today"
  }
];

export const INITIAL_INGREDIENTS: IngredientLog[] = [
  {
    id: "ing1",
    babyId: "baby-leo",
    name: "Steam-Roasted Carrot",
    reaction: "Loved it",
    date: "2023-10-23"
  },
  {
    id: "ing2",
    babyId: "baby-leo",
    name: "Apple Sauce",
    reaction: "Spat out",
    date: "2023-10-20"
  },
  {
    id: "ing3",
    babyId: "baby-leo",
    name: "Blueberry Mash",
    reaction: "Loved it",
    date: "2023-10-18"
  }
];

export const INITIAL_CHATS: ChatMessage[] = [
  {
    id: "c1",
    role: "assistant",
    content: "Hello! I've analyzed Leo's latest activity and growth profile. I noticed a slight height variance compared to the WHO median, but weight remains on a normal trajectory. Let me know if you need sleep schedule advice, solids recipes, or antipyretic dosage calculations!",
    timestamp: "11:46 AM"
  }
];

// LocalStorage helpers
export const loadState = <T>(key: string, defaultValue: T): T => {
  try {
    const saved = localStorage.getItem(key);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error("Error parsing localStorage key " + key, e);
  }
  return defaultValue;
};

export const saveState = <T>(key: string, value: T): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.error("Error writing to localStorage key " + key, e);
  }
};
