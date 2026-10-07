// The one source of truth for plans, credits and top-ups. All planned: nothing is for sale yet.
export interface Plan {
  id: 'pro' | 'max';
  name: string;
  price: number;        // USD per month
  line: string;
  credits: string;
  features: string[];
  featured?: boolean;
}

export const plans: Plan[] = [
  { id: 'pro', name: 'Pro', price: 20, line: 'For regular use.', credits: '22 credits per month',
    features: ['All six models.', 'Higher rate limits.', 'Top-ups at the same rates.'], featured: true },
  { id: 'max', name: 'Max', price: 100, line: 'For heavy use.', credits: '120 credits per month',
    features: ['All six models.', 'Highest rate limits.', 'Top-ups at the same rates.', 'Priority queue.'] },
];

export const creditUsd = 1;            // 1 credit = $1 of usage
export const topUps = [10, 50, 200];   // USD packs, at 1:1
export const creditExpiryMonths = 12;
/** Cheapest way in: the smallest top-up pack. */
export const entryUsd = Math.min(...topUps);
export const planStatus = 'planned';

/** "$10, $50 and $200" */
export const topUpList = () => topUps.map((n) => `$${n}`).join(', ').replace(/, ([^,]*)$/, ' and $1');
export const planPrice = (p: Plan) => `$${p.price}`;
