# Few-Shot Examples for Video-to-Article Conversion
# These examples demonstrate correct handling of common patterns

<examples>

<!-- ============================================ -->
<!-- EXAMPLE 1: Context Setting / Opening Setup   -->
<!-- ============================================ -->
<example name="context_preservation">
<description>
Shows how to capture the critical opening context that sets up the entire discussion.
This is what most summarizers miss.
</description>

<transcript_excerpt>
"So Andrej Karpathy tweeted something yesterday that kind of broke Twitter. He said—and I'm paraphrasing here—that most AI coding tools are basically just fancy autocomplete. And you know, at first I was like, that's kind of reductive, but then I started thinking about it more and... yeah, I actually think he's onto something, but he's also missing a huge piece of the puzzle. Let me explain what I mean."
</transcript_excerpt>

<correct_output>
## The Catalyst: Karpathy's "Autocomplete" Take

This discussion was sparked by a tweet from Andrej Karpathy that generated significant debate in the AI community. His claim: most AI coding tools are essentially "fancy autocomplete." 

The initial reaction might be to dismiss this as reductive—these tools do far more than traditional autocomplete. But there's a compelling argument that Karpathy has identified something important, while simultaneously missing crucial nuance. The following analysis unpacks both what he got right and what the take overlooks.
</correct_output>

<incorrect_output>
The speaker discusses AI coding tools and whether they're just autocomplete. They have mixed feelings about Karpathy's tweet.
</incorrect_output>

<why_correct_is_better>
- Captures WHO said it (Karpathy) and the IMPACT (broke Twitter)
- Preserves the speaker's evolving reaction ("at first... but then")
- Sets up the STRUCTURE of what follows (right + missing)
- Reads as article, not summary
</why_correct_is_better>
</example>


<!-- ============================================ -->
<!-- EXAMPLE 2: Code Reconstruction from Verbal   -->
<!-- ============================================ -->
<example name="code_reconstruction">
<description>
Shows how to transform verbal code descriptions into actual, formatted code blocks.
</description>

<transcript_excerpt>
"So the pattern here is you create a custom hook, let's call it useDebounce. It takes a value and a delay, both as parameters. Inside, you're gonna use useState to track the debounced value—initialize it with the value that was passed in. Then you set up a useEffect. In the effect, you create a timeout that calls setTimeout, and when it fires after the delay, you update the debounced value with setDebouncedValue. And here's the important part—you need to return a cleanup function that calls clearTimeout, otherwise you'll have stale timeouts firing. And then at the end of the hook, you just return the debouncedValue."
</transcript_excerpt>

<correct_output>
The recommended approach uses a custom React hook for debouncing values:

```typescript
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timeout);
  }, [value, delay]);

  return debouncedValue;
}
```

The critical implementation detail here is the cleanup function. Without returning `clearTimeout(timeout)` from the effect, previous timeouts would continue to fire even after the value changes, leading to stale updates and potential bugs.
</correct_output>

<incorrect_output>
The speaker explains how to create a useDebounce hook using useState and useEffect with a cleanup function.
</incorrect_output>

<why_correct_is_better>
- Provides ACTUAL CODE the reader can use
- Uses TypeScript (inferred from React context)
- Highlights the KEY INSIGHT (cleanup function importance)
- Reader learns the pattern without watching
</why_correct_is_better>
</example>


<!-- ============================================ -->
<!-- EXAMPLE 3: Preserving Opinions and Voice     -->
<!-- ============================================ -->
<example name="opinion_preservation">
<description>
Shows how to maintain the speaker's personality, opinions, and tone—including criticism.
</description>

<transcript_excerpt>
"Look, I'm just gonna say it—the React team has completely lost the plot with Server Components. Like, I get what they're trying to do, I really do. But the DX is absolutely terrible. You need a PhD just to understand when something runs on the server versus the client. And don't even get me started on the 'use client' directive spam. Every file. Every. Single. File. It's insane. I feel like we went from 'React is simple' to 'React requires a 200-page mental model' and nobody's talking about it."
</transcript_excerpt>

<correct_output>
The criticism of React Server Components is blunt: the React team has "completely lost the plot." The goals are understandable—better performance, smaller bundles, server-side data fetching. But the implementation has created a developer experience problem that's being under-discussed.

The core issue is cognitive overhead. Understanding whether code runs on the server or client now requires maintaining a complex mental model that didn't exist before. The proliferation of `'use client'` directives across codebases exemplifies this friction—it's become boilerplate noise in nearly every file.

The broader concern: React went from "simple" to requiring "a 200-page mental model," and the community hasn't fully reckoned with this complexity trade-off.
</correct_output>

<incorrect_output>
The speaker expresses concerns about React Server Components, noting that the developer experience could be improved and that understanding server vs. client execution can be challenging.
</incorrect_output>

<why_correct_is_better>
- Preserves the STRENGTH of the opinion ("lost the plot," "insane")
- Keeps the HUMOR ("need a PhD")
- Maintains the SPECIFIC complaints (use client spam)
- Doesn't sanitize criticism into corporate-speak
</why_correct_is_better>
</example>


<!-- ============================================ -->
<!-- EXAMPLE 4: Visual Reference Handling         -->
<!-- ============================================ -->
<example name="visual_reference">
<description>
Shows how to handle moments where the speaker references something shown on screen.
</description>

<transcript_excerpt>
"And if you look at this graph here—see this? The latency is totally fine, it's like sub-100 milliseconds up until about 10,000 concurrent connections. But then look what happens. See that cliff? Just absolutely tanks. We're talking 2, 3 seconds. That's where everything falls apart. This is why I keep saying you can't just throw horizontal scaling at every problem."
</transcript_excerpt>

<correct_output>
The performance characteristics reveal a critical threshold: latency remains acceptable (sub-100ms) up to approximately 10,000 concurrent connections. Beyond that point, performance degrades catastrophically—response times spike to 2-3 seconds. [Visual reference in video: speaker displays latency graph showing sharp degradation cliff at ~10K connections]

This cliff represents the system's practical scaling limit and illustrates a broader point: horizontal scaling isn't a universal solution. Some architectural bottlenecks can't be solved by adding more instances.
</correct_output>

<incorrect_output>
The speaker shows a graph demonstrating that latency increases significantly after 10,000 connections, suggesting that horizontal scaling has limits.
</incorrect_output>

<why_correct_is_better>
- Captures the SPECIFIC NUMBERS (sub-100ms, 10K, 2-3 seconds)
- Notes the visual clearly for readers who want to see it
- Extracts the INSIGHT/ARGUMENT (horizontal scaling limits)
- Doesn't just say "shows a graph"—describes what the graph shows
</why_correct_is_better>
</example>


<!-- ============================================ -->
<!-- EXAMPLE 5: Technical Explanation             -->
<!-- ============================================ -->
<example name="technical_explanation">
<description>
Shows how to preserve technical depth while making it readable.
</description>

<transcript_excerpt>
"So here's why RSCs actually matter architecturally. Before, you had this problem where—okay, let's say you have a dashboard, and that dashboard needs data from three different APIs. In the old model, either the client makes three round trips, which is slow, or you create this BFF—backend for frontend—that aggregates them, but now you're maintaining another service. With Server Components, the component itself can fetch directly from your database or internal services during render. The HTML shows up with the data already there. No loading spinners. No client-side fetch waterfalls. The mental model shift is: your component IS the BFF."
</transcript_excerpt>

<correct_output>
### The Architectural Argument for Server Components

The value proposition becomes clear when considering a common scenario: a dashboard that requires data from three different APIs.

**The Old Options:**

1. **Client-side fetching:** The browser makes three separate round trips after the page loads, creating visible loading states and fetch waterfalls.

2. **Backend for Frontend (BFF):** An intermediary service aggregates the API calls server-side, but now there's another service to build and maintain.

**The Server Component Solution:**

The component itself fetches data during server-side render—directly from databases or internal services. The HTML arrives with data already populated. No loading spinners. No client-side fetch waterfalls. No additional aggregation layer.

The mental model shift is significant: **the component becomes the BFF**. The data-fetching logic lives where the rendering logic lives, eliminating the architectural indirection.
</correct_output>

<incorrect_output>
Server Components allow data fetching during render, which can improve performance by avoiding client-side loading states. The speaker compares this to the BFF pattern.
</incorrect_output>

<why_correct_is_better>
- Preserves the FULL REASONING chain
- Uses formatting to show the COMPARISON clearly
- Keeps the KEY INSIGHT ("component IS the BFF")
- Reader understands WHY, not just WHAT
</why_correct_is_better>
</example>


<!-- ============================================ -->
<!-- EXAMPLE 6: Multiple Perspectives             -->
<!-- ============================================ -->
<example name="multiple_perspectives">
<description>
Shows how to handle nuanced takes that acknowledge multiple valid viewpoints.
</description>

<transcript_excerpt>
"Now, to be fair to the TypeScript team, I don't think they're wrong to be conservative here. If you're maintaining a type system used by millions of developers, you can't just yolo new features. But at the same time, the argument that 'it might break existing code' gets really old when the feature has been requested for seven years. At some point you gotta ask: who are you protecting? The five people with weird edge cases, or the thousands who would benefit? I don't have a clean answer here, honestly. Both sides have valid points."
</transcript_excerpt>

<correct_output>
### The TypeScript Conservatism Debate

The TypeScript team's caution is defensible: maintaining a type system used by millions requires conservative feature adoption. Breaking changes have outsized impact at that scale.

However, the "might break existing code" argument loses force when applied to features requested for seven years. The question becomes: whose interests are being protected? A small number of edge-case users, or the thousands who would benefit from the feature?

There's intellectual honesty in acknowledging this tension has no clean resolution. Both positions—"move carefully" and "at some point, ship it"—have legitimate merit. The disagreement is about where to draw the line, not whether a line should exist.
</correct_output>

<why_correct_is_better>
- Captures BOTH SIDES fairly
- Preserves the speaker's own uncertainty ("I don't have a clean answer")
- Frames it as a genuine TENSION, not a solved problem
- Doesn't pick a winner when the speaker didn't
</why_correct_is_better>
</example>

</examples>
