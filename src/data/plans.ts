// The one source of truth for subscription plans. All planned: nothing is for sale yet.
export interface Plan {
  id: 'free' | 'pro' | 'max';
  name: string;
  price: number;        // USD per month
  credits: string;
  features: string[];
  featured?: boolean;
}

export const plans: Plan[] = [
  { id: 'free', name: 'Free', price: 0, credits: '[COPY: trial credits]', features: ['[COPY: feature]', '[COPY: feature]'] },
  { id: 'pro', name: 'Pro', price: 20, credits: '[COPY: monthly credits]', features: ['[COPY: feature]', '[COPY: feature]', '[COPY: feature]'], featured: true },
  { id: 'max', name: 'Max', price: 100, credits: '[COPY: monthly credits]', features: ['[COPY: feature]', '[COPY: feature]', '[COPY: feature]'] },
];

export const planStatus = 'planned';
