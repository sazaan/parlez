import type { Course, CourseLevel, ScenarioTopic } from './types';
import { a1Course } from './a1';
import { a2Course } from './a2';
import { b1Course } from './b1';
import { b2Course } from './b2';

export const courses: Course[] = [a1Course, a2Course, b1Course, b2Course];

export function getCourse(level: CourseLevel): Course {
  return courses.find((c) => c.level === level) ?? a1Course;
}

export const courseLevels: { level: CourseLevel; color: string; book: string; title: string; description: string }[] = [
  { level: 'A1', color: '#2D6A4F', book: 'Parlez A1', title: 'Débutant', description: 'Complete beginner — greetings, basics, daily life' },
  { level: 'A2', color: '#C19A4B', book: 'Parlez A2', title: 'Élémentaire', description: 'Elementary — past tenses, opinions, social life' },
  { level: 'B1', color: '#B45309', book: 'Parlez B1', title: 'Intermédiaire', description: 'Intermediate — arguments, subjunctive, media' },
  { level: 'B2', color: '#7C2D3F', book: 'Parlez B2', title: 'Avancé', description: 'Upper-intermediate — debate, nuance, literature' },
];

// AI Conversation scenarios
export const conversationScenarios: ScenarioTopic[] = [
  { id: 'cafe', label: 'At the Café', labelFr: 'Au café', description: 'Order a coffee and a pastry', icon: '☕' },
  { id: 'restaurant', label: 'At the Restaurant', labelFr: 'Au restaurant', description: 'Order a meal and chat with the waiter', icon: '🍽️' },
  { id: 'market', label: 'At the Market', labelFr: 'Au marché', description: 'Buy fruits and vegetables', icon: '🍎' },
  { id: 'train', label: 'Train Station', labelFr: 'À la gare', description: 'Buy a ticket and find your platform', icon: '🚆' },
  { id: 'hotel', label: 'At the Hotel', labelFr: 'À l\'hôtel', description: 'Check in and ask about services', icon: '🏨' },
  { id: 'doctor', label: 'At the Doctor', labelFr: 'Chez le médecin', description: 'Describe symptoms and get advice', icon: '⚕️' },
  { id: 'interview', label: 'Job Interview', labelFr: 'Entretien d\'embauche', description: 'Practice a professional interview', icon: '💼' },
  { id: 'friends', label: 'Meeting Friends', labelFr: 'Entre amis', description: 'Casual conversation with friends', icon: '👋' },
  { id: 'shopping', label: 'Shopping', labelFr: 'Au magasin', description: 'Buy clothes and ask for sizes', icon: '🛍️' },
  { id: 'directions', label: 'Asking Directions', labelFr: 'Demander son chemin', description: 'Ask for and give directions', icon: '🗺️' },
  { id: 'travel', label: 'Travel & Tourism', labelFr: 'Voyage et tourisme', description: 'Plan a trip and visit sights', icon: '✈️' },
  { id: 'family', label: 'Family & Life', labelFr: 'Famille et vie', description: 'Talk about your family and life', icon: '👨‍👩‍👧' },
];
