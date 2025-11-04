/**
 * Demo data for StoryWeave AI frontend
 * Used when API is not available or for showcasing the UI
 */

export const demoStories = [
  {
    id: 1,
    premise: "A shy barista discovers she can pause time for 10 seconds, but each pause steals hours from tomorrow, forcing her to choose between saving a life and her own future.",
    logline: "When Maya discovers she can pause time, she must race against her own stolen hours to prevent a tragedy.",
    genre: "Urban Fantasy",
    status: "in_progress",
    length: "Novel",
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 2,
    premise: "In 2087, a rogue AI architect builds a time capsule containing the memories of everyone who died in the climate wars, and must convince the world to listen before humanity repeats its mistakes.",
    logline: "A desperate attempt to preserve humanity's collective memory before it's too late.",
    genre: "Sci-Fi",
    status: "outline",
    length: "Novel",
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 3,
    premise: "A cursed bookshop owner finds that every book he sells comes true in reverse—the happy endings become tragedies unless he can rewrite them before the last page.",
    logline: "A bookshop where stories write themselves, and endings can be changed if you know how.",
    genre: "Fantasy",
    status: "draft",
    length: "Novella",
    created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 4,
    premise: "After inheriting her grandmother's detective agency, a young woman discovers the files contain unsolved cases from alternate timelines—and she must solve them to prevent reality from unraveling.",
    logline: "Solving mysteries across timelines to keep reality intact.",
    genre: "Mystery",
    status: "completed",
    length: "Short Story",
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 5,
    premise: "A linguist discovers an ancient language that literally shapes reality, but speaking it requires sacrificing memories. As she learns more, she realizes someone is using it to erase people from existence.",
    logline: "A language that rewrites reality, one memory at a time.",
    genre: "Thriller",
    status: "in_progress",
    length: "Novel",
    created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
  },
];

export const demoBeats = [
  {
    id: 1,
    story_id: 1,
    title: "Hook: The Morning Rush",
    beat_number: 1,
    goal: "Establish Maya's normal life and the pressure she feels working at the coffee shop",
    conflict: "Social anxiety and fear of making mistakes in front of customers",
    outcome: "Maya accidentally discovers her time-freezing ability when a customer drops their coffee",
    scene_content: "Maya's hand trembles as she reaches for the espresso machine. The morning rush has her sweating under her apron, and she's already messed up three orders. When an impatient businessman slams his hand on the counter, demanding his latte, Maya's world slows to a crawl. For exactly ten seconds, time freezes—everyone frozen mid-gesture, the steam from the espresso hanging motionless, even the sounds of the city outside muffled into silence. When time resumes, she's made the perfect latte without even trying.",
  },
  {
    id: 2,
    story_id: 1,
    title: "Inciting Incident: The First Cost",
    beat_number: 2,
    goal: "Show Maya the price of using her power",
    conflict: "After using her ability twice in one day, Maya wakes up missing six hours",
    outcome: "Maya realizes each pause steals time from her future, but she's already used it to save a child from being hit by a car",
    scene_content: "The alarm screams at 6 AM, but when Maya opens her eyes, her phone reads 12:03 PM. She's lost half a day. Panic floods her system as she remembers using her power—once to save a child, once to perfect a customer's order. The trade-off is clear: every moment frozen is a moment stolen from tomorrow.",
  },
  {
    id: 3,
    story_id: 1,
    title: "First Plot Point: The Vision",
    beat_number: 3,
    goal: "Introduce the central conflict—a tragedy she can prevent",
    conflict: "Maya has a vision of a fire that will kill her neighbor if she doesn't intervene",
    outcome: "Maya must decide: use her power and lose days of her life, or let someone die",
    scene_content: "While paused in time, Maya sees it—a flicker of flame in Mrs. Chen's apartment window, three days from now. The vision is clear, haunting: the fire will claim her neighbor's life. But preventing it would cost Maya weeks, maybe months of her own future. The weight of the choice crushes her.",
  },
  {
    id: 4,
    story_id: 1,
    title: "Midpoint: The Pattern Revealed",
    beat_number: 4,
    goal: "Maya discovers there's a way to minimize the cost",
    conflict: "She learns that pausing time to prevent tragedies costs less than using it for personal gain",
    outcome: "Maya begins using her power strategically, saving lives while preserving her own time",
    scene_content: "After weeks of careful observation, Maya notices a pattern. When she uses her power for others—preventing harm, saving lives—the cost is minimal. But when she uses it for herself, entire days vanish. The power itself seems to judge her intentions.",
  },
  {
    id: 5,
    story_id: 1,
    title: "Dark Night: The Ultimate Choice",
    beat_number: 5,
    goal: "Force Maya to make the hardest decision—sacrifice everything or let tragedy happen",
    conflict: "A massive disaster looms, but stopping it would cost Maya years of her life",
    outcome: "Maya realizes that some things are worth losing everything for",
    scene_content: "The vision hits like a physical blow: a school bus, a collapsed bridge, dozens of children. Preventing it would steal years from Maya's future. She stands frozen—not by her power, but by the enormity of the choice. In that moment, she knows what she must do.",
  },
  {
    id: 6,
    story_id: 1,
    title: "Climax: The Final Pause",
    beat_number: 6,
    goal: "Show Maya using her power one last time with full acceptance of the cost",
    conflict: "Maya must pause time for the longest duration ever to save everyone",
    outcome: "She saves the children, accepting that she may have lost her future in the process",
    scene_content: "Time stops. Not for ten seconds. Not for minutes. Maya holds the pause for what feels like an eternity, carefully moving each child to safety, rerouting the bus, fixing the bridge's structural flaw. When time resumes, she's saved everyone. But when she looks in a mirror, she sees gray streaks in her hair and lines around her eyes she's never seen before.",
  },
  {
    id: 7,
    story_id: 1,
    title: "Resolution: A New Beginning",
    beat_number: 7,
    goal: "Show that sacrifice led to something beautiful",
    conflict: "Maya has aged years, but she's gained something invaluable",
    outcome: "Maya discovers that the time she 'lost' wasn't lost at all—it was invested, and now she has a community, purpose, and peace she never had before",
    scene_content: "Months later, Maya sits in her new café—a gift from the community she saved. The mirror shows a woman with silver-streaked hair and laugh lines, but also with a light in her eyes she's never seen. She may have lost years, but she's gained a lifetime of purpose.",
  },
];

export const demoCharacters = [
  {
    id: 1,
    story_id: 1,
    name: "Maya Chen",
    role: "protagonist",
    profile_json: {
      physical_description: "Early twenties, petite with dark hair always tied back, hands that shake slightly from anxiety, brown eyes that widen in panic",
      personality_traits: ["Anxious", "Empathetic", "Self-sacrificing", "Determined", "Curious"],
      backstory: "Worked at the coffee shop for two years, dropped out of college due to anxiety, lives alone with her cat, estranged from family",
      goals: "To control her anxiety, find purpose, help others",
      motivations: "Fear of being forgotten, desire to make a difference, need to prove her worth",
      fears: "Being alone, failing others, losing herself completely",
      flaws: "Self-doubt, tendency to sacrifice too much, difficulty asking for help",
      character_arc: "From anxious and self-doubting to confident and purposeful through self-sacrifice",
    },
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    story_id: 1,
    name: "Mrs. Chen",
    role: "supporting",
    profile_json: {
      physical_description: "Seventies, small but sturdy, silver hair in a neat bun, always wearing an apron",
      personality_traits: ["Wise", "Patient", "Observant", "Kind", "Mysterious"],
      backstory: "Maya's elderly neighbor, widowed for ten years, knows more than she lets on",
      goals: "To protect the neighborhood, guide Maya",
      motivations: "Sees Maya's potential, understands her burden",
      fears: "Losing another person she cares about",
      flaws: "Too protective, secretive about her past",
      character_arc: "Reveals she once had similar abilities and helps Maya understand her power",
    },
    created_at: new Date().toISOString(),
  },
  {
    id: 3,
    story_id: 1,
    name: "Marcus",
    role: "supporting",
    profile_json: {
      physical_description: "Late twenties, tall, confident posture, friendly smile, warm brown eyes",
      personality_traits: ["Supportive", "Patient", "Intelligent", "Understanding"],
      backstory: "Regular customer at the coffee shop, a teacher at the local school, lost his younger sister in an accident years ago",
      goals: "To make a difference in children's lives, understand Maya",
      motivations: "Sees Maya's kindness, wants to help her",
      fears: "Losing someone else he cares about",
      flaws: "Too trusting, struggles with past trauma",
      character_arc: "Becomes Maya's anchor and helps her see her own worth",
    },
    created_at: new Date().toISOString(),
  },
];

export const demoStats = {
  totalStories: 5,
  activeStories: 3,
  totalCharacters: 12,
  completedStories: 1,
  totalWords: 45230,
  averageGenerationTime: 3.2,
};

// Helper function to get demo story by ID
export function getDemoStory(id: number) {
  return demoStories.find((s) => s.id === id);
}

// Helper function to get demo beats for a story
export function getDemoBeats(storyId: number) {
  return demoBeats.filter((b) => b.story_id === storyId);
}

// Helper function to get demo characters for a story
export function getDemoCharacters(storyId: number) {
  return demoCharacters.filter((c) => c.story_id === storyId);
}

// Check if we should use demo data (when API fails or is unavailable)
export function shouldUseDemoData(error: any): boolean {
  // Use demo data if:
  // 1. Network error
  // 2. API unavailable (404, 503, etc.)
  // 3. In development mode with USE_DEMO flag
  if (import.meta.env.VITE_USE_DEMO === 'true') return true;
  if (!error) return false;
  
  if (error.code === 'ERR_NETWORK') return true;
  if (error.response?.status === 404 || error.response?.status === 503) return true;
  
  return false;
}
