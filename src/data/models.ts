// The one source of truth for the catalogue. Every model here is fictional (see AGENTS.md).
export interface Model {
  id: string;
  name: string;
  tagline: string;
  context: number;      // tokens
  inputPrice: number;   // USD per 1M input tokens
  outputPrice: number;  // USD per 1M output tokens
  tags: string[];
  fictional: true;
}

export const models: Model[] = [
  { id: 'abliterate-dong-flash-v2.3', name: 'Dong Flash v2.3', tagline: '[COPY: tagline]', context: 32_000, inputPrice: 0.1, outputPrice: 0.3, tags: ['fast', 'chat'], fictional: true },
  { id: 'abliterate-house-md-v5.2', name: 'House MD v5.2', tagline: '[COPY: tagline]', context: 128_000, inputPrice: 0.8, outputPrice: 2.4, tags: ['reasoning'], fictional: true },
  { id: 'abliterate-sonny-v2.5', name: 'Sonny v2.5', tagline: '[COPY: tagline]', context: 64_000, inputPrice: 0.3, outputPrice: 0.9, tags: ['chat', 'roleplay'], fictional: true },
  { id: 'abliterate-antrax-v3.0', name: 'Antrax v3.0', tagline: '[COPY: tagline]', context: 128_000, inputPrice: 1.2, outputPrice: 3.6, tags: ['code', 'reasoning'], fictional: true },
  { id: 'abliterate-mable-v4.2', name: 'Mable v4.2', tagline: '[COPY: tagline]', context: 64_000, inputPrice: 0.4, outputPrice: 1.2, tags: ['writing'], fictional: true },
  { id: 'abliterate-soul-5.5', name: 'Soul 5.5', tagline: '[COPY: tagline]', context: 200_000, inputPrice: 3, outputPrice: 9, tags: ['flagship', 'reasoning'], fictional: true },
];

export const usd = (n: number) => `$${n.toFixed(2)}`;
export const ctx = (n: number) => `${Math.round(n / 1000)}K`;
