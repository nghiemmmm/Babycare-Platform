import { BabyProfile, Gender, Measurement, MedicationLog, Guardian, FeedLog, IngredientLog, ChatMessage } from "./types";

export const INITIAL_BABIES: BabyProfile[] = [
  {
    id: "baby-leo",
    name: "Leo",
    birthDate: "2023-04-20",
    gender: Gender.Boy,
    avatarUrl: "/static/img/leo.png",
    isActive: true,
    allergies: ["Đậu nành"]
  },
  {
    id: "baby-bo",
    name: "Bo",
    birthDate: "2023-11-15",
    gender: Gender.Girl,
    avatarUrl: "/static/img/bo.png",
    isActive: false,
    allergies: []
  }
];

export const INITIAL_MEASUREMENTS: Measurement[] = [
  {
    id: "m6",
    babyId: "baby-leo",
    date: "2023-10-24",
    ageInMonths: 6,
    weight: 7.2,
    height: 66,
    headCircumference: 42.5,
    status: "Height Alert (Risk of Stunting)",
    notes: "Leo có chiều cao tiệm cận chuẩn dưới WHO (bằng percentile 15), cân nặng chuẩn 7.2kg. Bác sĩ tư vấn tiếp tục bổ sung Vitamin D3 K2 và tập tummy time tích cực."
  },
  {
    id: "m5",
    babyId: "baby-leo",
    date: "2023-09-20",
    ageInMonths: 5,
    weight: 6.8,
    height: 64,
    headCircumference: 41.8,
    status: "Normal",
    notes: "Tiến trình tăng trưởng ổn định."
  },
  {
    id: "m4",
    babyId: "baby-leo",
    date: "2023-08-15",
    ageInMonths: 4,
    weight: 6.6,
    height: 63.2,
    headCircumference: 41.5,
    status: "Normal",
    notes: "Tăng trưởng thể lực tốt."
  },
  {
    id: "m3",
    babyId: "baby-leo",
    date: "2023-07-20",
    ageInMonths: 3,
    weight: 6.2,
    height: 61,
    headCircumference: 40.5,
    status: "Normal",
    notes: "Đạt mốc lẫy thành thạo."
  }
];

export const INITIAL_MEDICATIONS: MedicationLog[] = [
  {
    id: "med1",
    babyId: "baby-leo",
    name: "Hapacol 150mg (Paracetamol)",
    dosage: "150mg (1 gói)",
    time: "11:45 AM",
    date: "Today",
    prescribedBy: "Dr. Aris (Nhi khoa)"
  },
  {
    id: "med2",
    babyId: "baby-leo",
    name: "Vitamin D3 K2",
    dosage: "2 giọt",
    time: "08:00 AM",
    date: "Today",
    prescribedBy: "Bổ sung hàng ngày"
  },
  {
    id: "med3",
    babyId: "baby-leo",
    name: "Siro ho thảo dược Prospan",
    dosage: "2.5ml",
    time: "02:00 PM",
    date: "Today",
    prescribedBy: "Dr. Aris (Nhi khoa)"
  }
];

export const INITIAL_GUARDIANS: Guardian[] = [
  {
    id: "g1",
    name: "Minh Anh (Mẹ)",
    email: "nghiem@babycare.com",
    role: "ADMIN",
    status: "Synced"
  },
  {
    id: "g2",
    name: "Hoàng Nam (Bố)",
    email: "hoangnam@family.vn",
    role: "GUARDIAN",
    status: "Synced"
  },
  {
    id: "g3",
    name: "Bà Nội Kim Yến",
    email: "kimyen.grandma@family.vn",
    role: "VIEWER",
    status: "Invited"
  }
];

export const INITIAL_FEEDS: FeedLog[] = [
  {
    id: "feed1",
    babyId: "baby-leo",
    type: "Formula",
    details: "180ml Sữa Nan Optipro 2",
    amount: 180,
    time: "01:00 PM",
    date: "Today"
  },
  {
    id: "feed2",
    babyId: "baby-leo",
    type: "Solids",
    details: "Bột ăn dặm Yến mạch + Táo tây hấp nghiền",
    amount: 1,
    time: "10:30 AM",
    date: "Today"
  },
  {
    id: "feed3",
    babyId: "baby-leo",
    type: "Breast",
    details: "Sữa mẹ bú trực tiếp (Bên trái 15 phút)",
    amount: 120,
    time: "08:00 AM",
    date: "Today"
  }
];

export const INITIAL_INGREDIENTS: IngredientLog[] = [
  {
    id: "ing1",
    babyId: "baby-leo",
    name: "🍎 Táo tây hấp nghiền",
    reaction: "Loved it",
    date: "2023-10-23"
  },
  {
    id: "ing2",
    babyId: "baby-leo",
    name: "🥣 Bột yến mạch mịn",
    reaction: "Loved it",
    date: "2023-10-20"
  },
  {
    id: "ing3",
    babyId: "baby-leo",
    name: "🥕 Cà rốt luộc nghiền",
    reaction: "Neutral",
    date: "2023-10-18"
  },
  {
    id: "ing4",
    babyId: "baby-leo",
    name: "🚨 Sữa đậu nành & Đậu phụ",
    reaction: "Allergic Reaction",
    date: "2023-10-10"
  }
];

export const INITIAL_CHATS: ChatMessage[] = [
  {
    id: "c1",
    role: "assistant",
    content: "Chào mẹ Minh Anh! Em đã kiểm tra hồ sơ của bé Leo (6 tháng tuổi). Leo đang có chiều cao 66cm và cân nặng 7.2kg. Do bé có tiền sử **Dị ứng Đậu nành**, em đã tự động loại bỏ các thực phẩm chứa Soy Protein trong thực đơn khuyến nghị. Mẹ có muốn tham khảo các công thức ăn dặm giàu canxi không chứa đậu nành không ạ?",
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
