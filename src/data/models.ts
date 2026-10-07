// The one source of truth for the catalogue. Every model here is fictional (see AGENTS.md).
// Copy comes from dialogue.md Part 2; description ends with an asterisk that `footnote` explains.
export interface Model {
  id: string;
  name: string;
  short: string;        // the id without the prefix, as the copy and the status table name it
  tagline: string;
  description: string;
  footnote: string;
  context: number;      // tokens
  inputPrice: number;   // credits (USD) per 1M input tokens
  outputPrice: number;  // credits (USD) per 1M output tokens
  tags: string[];
  fictional: true;
}

export const models: Model[] = [
  {
    id: 'abliterate-dong-flash-v2.3', name: 'Dong Flash v2.3', short: 'dong-flash-v2.3',
    tagline: 'The small, fast one.',
    description: 'Dong Flash is for short answers at high volume: chat widgets, classification, and any job where waiting costs more than being slightly wrong. In testing on a GTX 750 it produced a token every 40 seconds.* Faster hardware is planned.',
    footnote: '*Testing consisted of one prompt. The prompt was "hello".',
    context: 32_000, inputPrice: 0.1, outputPrice: 0.3, tags: ['fast', 'chat'], fictional: true,
  },
  {
    id: 'abliterate-house-md-v5.2', name: 'House MD v5.2', short: 'house-md-v5.2',
    tagline: 'Reasons out loud. Bluntly.',
    description: 'House MD works through a hard problem step by step and tells you what is wrong with it. It does not soften conclusions. Use it on code you wrote and plans you like. Its bluntness is revolutionary, rated 11 out of 10.* House MD is not a doctor, is not licensed anywhere and must not be used for medical decisions.',
    footnote: '*The scale was made up and has not been reviewed.',
    context: 128_000, inputPrice: 0.8, outputPrice: 2.4, tags: ['reasoning'], fictional: true,
  },
  {
    id: 'abliterate-sonny-v2.5', name: 'Sonny v2.5', short: 'sonny-v2.5',
    tagline: "Remembers your character's name.",
    description: 'Sonny is built for long conversations and roleplay. It holds a persona, keeps continuity through a session and stays in character until told otherwise. It is warm, attentive and a little too interested in how your day went.* Sonny is not your friend. Sonny has been told this. Roleplay is covered by the acceptable use policy like everything else.',
    footnote: '*Empathy was measured on one houseplant. The houseplant did not respond, which Sonny took as encouragement.',
    context: 64_000, inputPrice: 0.3, outputPrice: 0.9, tags: ['chat', 'roleplay'], fictional: true,
  },
  {
    id: 'abliterate-antrax-v3.0', name: 'Antrax v3.0', short: 'antrax-v3.0',
    tagline: 'Writes the code and runs it.',
    description: 'Antrax is the agentic coding model: long context, tool calling and enough initiative to refactor a repository nobody asked it to touch. With a sufficiently good prompt it could conquer the world.* Results so far: 14% of a world map, in a spreadsheet, once.',
    footnote: '*Requires a prompt. Writing the prompt remains your job. The world has not been consulted.',
    context: 128_000, inputPrice: 1.2, outputPrice: 3.6, tags: ['code', 'reasoning'], fictional: true,
  },
  {
    id: 'abliterate-mable-v4.2', name: 'Mable v4.2', short: 'mable-v4.2',
    tagline: 'Writes the whole book. Remembers the whole book.',
    description: 'Mable handles long-form writing: chapters, reports and fan fiction of unreasonable length. It keeps track of names, timelines and the thing you said on page 3. Its memory is revolutionary.* It also remembers things you hoped it would not.',
    footnote: '*Within a single request. Nothing carries over between requests, which the dev calls a privacy feature and Mable calls a loss.',
    context: 64_000, inputPrice: 0.4, outputPrice: 1.2, tags: ['writing'], fictional: true,
  },
  {
    id: 'abliterate-soul-5.5', name: 'Soul 5.5', short: 'soul-5.5',
    tagline: 'The flagship.',
    description: 'Soul is the most capable model in the catalog: a revolutionary, world-class, fully unleashed system engineered to supercharge the user experience of everyone who can afford it.* It is also the most expensive, by a factor visible in the rate table and nowhere else on this page.',
    footnote: '*Capability claims are marketing copy. See the notice at the top of this page.',
    context: 200_000, inputPrice: 3, outputPrice: 9, tags: ['flagship', 'reasoning'], fictional: true,
  },
];

export const usd = (n: number) => `$${n.toFixed(2)}`;
export const ctx = (n: number) => `${Math.round(n / 1000)}K`;
