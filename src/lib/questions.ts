export interface Question {
  id: string;
  title: string;
  category: "system_design" | "ml_system_design";
  difficulty: "easy" | "medium" | "hard";
  brief: string;
  hints: string[];
}

export const QUESTIONS: Question[] = [
  {
    id: "dropbox",
    title: "Design Dropbox",
    category: "system_design",
    difficulty: "hard",
    brief:
      "Design a file storage and sync service. Users upload files from any device, see them on every other device, and can share files with other users. Files can be very large (multi-GB). Network conditions are unreliable.",
    hints: [
      "Think about chunking, resumable uploads, dedup, and metadata vs blob storage.",
      "How do you sync changes efficiently without re-downloading everything?",
    ],
  },
  {
    id: "twitter-feed",
    title: "Design Twitter / X Home Feed",
    category: "system_design",
    difficulty: "hard",
    brief:
      "Design the home timeline. Users post short messages, follow other users, and see a personalized feed of recent posts from people they follow. Read-heavy: the feed is loaded far more often than posts are written. Some users have millions of followers.",
    hints: [
      "Fanout-on-write vs fanout-on-read — and the hybrid for celebrity accounts.",
      "How do you keep p99 feed latency low?",
    ],
  },
  {
    id: "url-shortener",
    title: "Design a URL Shortener (bit.ly)",
    category: "system_design",
    difficulty: "easy",
    brief:
      "Design a service that converts long URLs into short ones (e.g. bit.ly/abc123). Clicking a short link redirects to the original URL. Track click counts. Read traffic dwarfs write traffic.",
    hints: [
      "How do you generate short codes uniquely at scale without collisions?",
      "Where do redirects get cached, and what's the consistency model?",
    ],
  },
  {
    id: "ml-recommender",
    title: "Design an ML-Powered Recommendation System (e.g. YouTube)",
    category: "ml_system_design",
    difficulty: "hard",
    brief:
      "Design a recommendation system that suggests videos to users on a platform with billions of items. Latency must be low (<200ms p99). Cold-start users and new items must still get reasonable recommendations. The system must handle continuous learning from user feedback.",
    hints: [
      "Two-stage: candidate generation (recall) + ranking (precision). Where do embeddings live?",
      "How do you handle online vs offline features and avoid training/serving skew?",
    ],
  },
  {
    id: "ml-fraud",
    title: "Design an ML Fraud Detection System",
    category: "ml_system_design",
    difficulty: "hard",
    brief:
      "Design a real-time fraud detection system for payments. Decisions must come back in <50ms. False positives anger customers; false negatives lose money. The label is delayed (chargebacks come days later). Adversaries actively try to evade the model.",
    hints: [
      "Online features (recent velocity) vs offline features — feature store design.",
      "How do you evaluate and retrain when ground truth is delayed by days?",
    ],
  },
];

export function questionById(id: string): Question | undefined {
  return QUESTIONS.find((q) => q.id === id);
}
